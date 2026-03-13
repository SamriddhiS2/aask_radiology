import paramiko
import os
import logging
import cleanup

logging.basicConfig(level=logging.INFO)

HOST = "172.25.197.29"
PORT = 22
REMOTE_FOLDER = os.sep + os.path.join("", "home", "oscarresearch", "DICOMin", "ToProcess")

def calculate_total_size(local_folder):
    """
    calculate_total_size calculates the total size of local_folder for the progress bar.
    """
    total_bytes = 0
    for root, _, files in os.walk(local_folder):
        for file in files:
            total_bytes += os.path.getsize(os.path.join(root, file))
    return total_bytes

def create_dir_on_oscar(sftp, remote_path):
    """
    create_dir_on_oscar creates directories on OSCAR so that files can be uploaded to it.
    """
    # Ensure remote directory exists
    try:
        sftp.stat(remote_path)
    except FileNotFoundError:
        sftp.mkdir(remote_path)
        logging.info(f"Created directory on OSCAR: {remote_path}.")

def upload_folder_sftp(uw_id, local_folder, upload_to_oscar_progress_bar, upload_to_oscar_progress_label, prepare_oscar_progress_bar, prepare_oscar_progress_label):
    """
    upload_folder_sftp is in charge of connecting to OSCAR and uploading files using SFTP. It 
    will first clean up the remote_path folder and then walk through the local_folder to copy files to OSCAR.
    It will copy files to /home/oscarresearch/DICOMin/ToProcess.
    """
    logging.info(f"Local folder: {local_folder}, UW NET ID: {uw_id}.")
    total_size_bytes = calculate_total_size(local_folder)
    upload_to_oscar_progress_bar["maximum"] = total_size_bytes
    uploaded_bytes = 0

    # Connect to SFTP
    oscar_username = os.getenv('OSCAR_USERNAME')
    oscar_password = os.getenv('OSCAR_PASSWORD')
    if oscar_username is None or oscar_password is None:
        raise Exception("Please enter OSCAR_USERNAME and OSCAR_PASSWORD in your environment variable")
    
    transport = paramiko.Transport((HOST, PORT))
    transport.connect(username=oscar_username, password=oscar_password)
    sftp = paramiko.SFTPClient.from_transport(transport)

    remote_path_with_uw_net_id = os.path.join(REMOTE_FOLDER, uw_id)
    logging.info(f"Remote path directory with UW NET ID: {remote_path_with_uw_net_id}")
    cleanup.remove_previous_output_dir_on_oscar(sftp, remote_path_with_uw_net_id.replace("\\", "/"), prepare_oscar_progress_bar, prepare_oscar_progress_label)
    create_dir_on_oscar(sftp, remote_path_with_uw_net_id.replace("\\", "/"))

    # Walk through local directory
    for root, _, files in os.walk(local_folder):
        # Enable the next line for debugging!
        # logging.debug(f"Root: {root}, Files: {files}.")

        # Compute relative path and remote path
        relative_path = os.path.relpath(root, local_folder)
        remote_path = os.path.join(remote_path_with_uw_net_id, relative_path).replace("\\", "/")
        create_dir_on_oscar(sftp, remote_path)

        # Upload files in the current directory
        for file in files:
            local_file = os.path.join(root, file)
            remote_file = os.path.join(remote_path, file).replace("\\", "/")
            file_size = os.path.getsize(local_file)
            sftp.put(local_file, remote_file)
            uploaded_bytes += file_size
            upload_to_oscar_progress_bar.after(0, upload_to_oscar_progress_bar.step, file_size)
            percent = int((uploaded_bytes / total_size_bytes) * 100)
            upload_to_oscar_progress_label.after(0, upload_to_oscar_progress_label.config, {'text': f"Progress: {percent}%"})
            
            # Enable the next line for debugging!
            # logging.debug(f"Uploaded: {local_file} -> {remote_file}.")

    sftp.close()
    transport.close()
    logging.info("Upload complete.")