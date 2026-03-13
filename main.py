import eel
import os
import tkinter as tk
from tkinter import filedialog
import parsedicom
import uploadtooscar
import sys
import signal
import cleanup

eel.init('web')

def close_callback(page, sockets):
    print("Browser window closed. Exiting application.")
    sys.exit(0)

def handle_ctrl_c(sig, frame):
    print("\nCtrl+C detected. Closing application...")
    if eel._websockets:
        eel.spawn(eel.close_window)
    sys.exit(0)

@eel.expose
def select_source_folder():
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title="Select Source DICOM Folder")
    return folder_path

@eel.expose
def start_processing(uw_net_id, source_dir, target_series_list):
    if not source_dir:
        eel.update_status("Error: Source folder not provided.")()
        return
    try:
        output_dir = os.path.dirname(source_dir)
        print(f"Starting parsing for: {target_series_list}")
        parsing_message = parsedicom.run_parsing_process(
            source_dir,
            output_dir,
            target_series_list,
            lambda value, total: eel.update_progress('parse', value, total)(),
            lambda percent: eel.update_progress_label('parse', percent)()
        )
        if "Success" not in parsing_message:
            eel.update_status(parsing_message)()
            eel.processing_finished()()
            return
        upload_folder = os.path.join(output_dir, parsedicom.OUTPUT_FOLDER_NAME)
        print(f"Starting upload from: {upload_folder}")
        uploadtooscar.upload_folder_sftp(
            uw_net_id,
            upload_folder,
            lambda value, total: eel.update_progress('clean', value, total)(),
            lambda percent: eel.update_progress_label('clean', percent)(),
            lambda value, total: eel.update_progress('upload', value, total)(),
            lambda percent: eel.update_progress_label('upload', percent)()
        )
        eel.update_status("Processing complete! Files parsed and uploaded successfully.")()
    except Exception as e:
        print(f"An error occurred: {e}")
        eel.update_status(f"An error occurred: {e}")()
    finally:
        eel.processing_finished()()

def run_parsing_process_modified(source_dir, output_dir, target_series, update_progress_func, update_label_func):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    (tasks, num_patients) = parsedicom.find_files_to_copy(source_dir, output_dir, target_series)
    max_workers = os.cpu_count() or 4
    if tasks:
        cleanup.remove_series_selection_output_dir(os.path.join(output_dir, parsedicom.OUTPUT_FOLDER_NAME))
        total = len(tasks)
        print(f"\nCopying files with {max_workers} parallel workers")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(parsedicom.copy_file, task) for task in tasks]
            for i, _ in enumerate(as_completed(futures), 1):
                update_progress_func(i, total)
                percent = int((i / total) * 100)
                update_label_func(f"Progress: {percent}%")
        return f"Success! Files for {num_patients} patients were parsed."
    else:
        return "Failure! Series does not exist in source folder."

def upload_folder_sftp_modified(uw_net_id, local_folder, clean_progress_func, clean_label_func, update_progress_func, update_label_func):
    import paramiko
    try:
        total_size_bytes = uploadtooscar.calculate_total_size(local_folder)
        uploaded_bytes = 0
        oscar_username = os.getenv('OSCAR_USERNAME')
        oscar_password = os.getenv('OSCAR_PASSWORD')
        if oscar_username is None or oscar_password is None:
            raise Exception("Please enter OSCAR_USERNAME and OSCAR_PASSWORD in your environment variable")
        transport = paramiko.Transport((uploadtooscar.HOST, uploadtooscar.PORT))
        transport.connect(username=oscar_username, password=oscar_password)
        sftp = paramiko.SFTPClient.from_transport(transport)

        remote_path_with_uw_net_id = os.path.join(uploadtooscar.REMOTE_FOLDER, uw_net_id)
        cleanup.remove_previous_output_dir_on_oscar_modified(sftp, remote_path_with_uw_net_id.replace("\\", "/"), clean_progress_func, clean_label_func)
        uploadtooscar.create_dir_on_oscar(sftp, remote_path_with_uw_net_id.replace("\\", "/"))

        for root, _, files in os.walk(local_folder):
            relative_path = os.path.relpath(root, local_folder)
            remote_path = os.path.join(remote_path_with_uw_net_id, relative_path).replace("\\", "/")
            uploadtooscar.create_dir_on_oscar(sftp, remote_path)
            
            for file in files:
                local_file = os.path.join(root, file)
                remote_file = os.path.join(remote_path, file).replace("\\", "/")
                file_size = os.path.getsize(local_file)
                sftp.put(local_file, remote_file)
                uploaded_bytes += file_size
                update_progress_func(uploaded_bytes, total_size_bytes)
                percent = int((uploaded_bytes / total_size_bytes) * 100) if total_size_bytes > 0 else 0
                update_label_func(f"Progress: {percent}%")
    
        sftp.close()
        transport.close()
        print("Upload complete.")
    except Exception as e:
        print(f"Error during upload: {e}")
        raise e

parsedicom.run_parsing_process = run_parsing_process_modified
uploadtooscar.upload_folder_sftp = upload_folder_sftp_modified

if __name__ == '__main__':
    signal.signal(signal.SIGINT, handle_ctrl_c)

    print("Starting AASK application. Press Ctrl+C or close the browser window  to exit.")
    if getattr(sys, 'frozen', False):
        # Running as compiled
        base_path = sys._MEIPASS
    else:
        # Running as script
        base_path = os.path.abspath(".")

    eel.init(os.path.join(base_path, 'web'))
    eel.start('index.html', size=(1200, 850), position=(200, 100), close_callback=close_callback)