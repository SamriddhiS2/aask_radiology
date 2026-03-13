import pydicom # type: ignore
import os
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
import cleanup
import logging

logging.basicConfig(level=logging.INFO)

OUTPUT_FOLDER_NAME = "dicom_series_parser_output"

def clean_name(s):
    return str(s).replace(" ", "_").replace("^", "_").replace("/", "_").replace(":", "_")

def find_files_to_copy(source_dir, output_dir, target_series):
    """
    find_files_to_copy is in charge of parsing the DICOM files in source_dir and creating a new 
    folder in output_dir. It will find images in target_series by using the DICOM 
    directory (DICOMDIR) that is generated from visage exports. It will output the source file
    that should be copied and the directory that the file should be copied to.
    """
    copy_tasks = []
    patients = set()
    num_patients = 0

    if not os.path.isdir(source_dir):
        logging.error("Source directory for series selection is not found.")
        raise Exception("Source directory for series selection is not found.")

    for study_folder_name in os.listdir(source_dir):
        study_folder_path = os.path.join(source_dir, study_folder_name)
        if not os.path.isdir(study_folder_path):
            continue
        
        dicomdir_path = os.path.join(study_folder_path, "DICOMDIR")
        if not os.path.exists(dicomdir_path):
            continue
        
        dicomdir = pydicom.dcmread(dicomdir_path, stop_before_pixels=True)
        
        current_patient, current_study, include_images = "UnknownPatient", "UnknownStudy", False

        for record in dicomdir.DirectoryRecordSequence:
            record_type = record.DirectoryRecordType
            if record_type == "PATIENT":
                current_patient = clean_name(getattr(record, "PatientName", "UnknownPatient"))
            elif record_type == "STUDY":
                current_study = clean_name(getattr(record, "StudyDescription", "UnknownStudy"))
            elif record_type == "SERIES":
                series = getattr(record, "SeriesDescription", "")
                include_images = series in target_series
            elif record_type == "IMAGE" and include_images:
                patients.add(current_patient)
                relative_path_parts = record.ReferencedFileID
                source_file_path = os.path.join(study_folder_path, *relative_path_parts)
                dest_folder = os.path.join(output_dir, OUTPUT_FOLDER_NAME, current_patient, current_study, clean_name(series))
                copy_tasks.append((source_file_path, dest_folder))
    
    num_patients = len(patients)
    logging.info(f"Found DICOM files for the following patients: {patients}")
    logging.info(f"Found {len(copy_tasks)} files to copy for {num_patients} patients.")
    return (copy_tasks, num_patients)

def copy_file(task):
    """
    copy_file will actually copy the file from source_path to dest_folder
    """
    source_path, dest_folder = task
    if os.path.exists(source_path):
        os.makedirs(dest_folder, exist_ok=True)
        copied_file = shutil.copy2(source_path, dest_folder)
        new_path = copied_file + ".dcm"
        os.rename(copied_file, new_path)
        return True
    return False

def run_parsing_process(source_dir, output_dir, target_series, progress_bar, progress_label):
    """
    run_parsing_process will find all the files that need to be copied using as many CPU
    threads that it can.
    """
    (tasks, num_patients) = find_files_to_copy(source_dir, output_dir, target_series)
    max_workers = os.cpu_count() or 1
    if tasks:
        cleanup_dir = os.path.join(output_dir, OUTPUT_FOLDER_NAME)
        cleanup.remove_series_selection_output_dir(cleanup_dir)

        total = len(tasks)
        progress_bar["maximum"] = total

        logging.info(f"\nCopying files with {max_workers} parallel workers.")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(copy_file, task) for task in tasks]
            for i, _ in enumerate(as_completed(futures), 1):
                progress_bar.after(0, progress_bar.step, 1)
                percent = int((i / total) * 100)
                progress_label.after(0, progress_label.config, {'text': f"Progress: {percent}%"})
        return num_patients
    else:
        raise Exception("The series you selected does not exist in the source folder.")