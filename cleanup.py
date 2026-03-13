import os
import shutil
import stat
import logging

logging.basicConfig(level=logging.INFO)

def remove_series_selection_output_dir(output_dir):
    """
    Cleans up local directory that was created for series selection
    """
    if os.path.exists(output_dir) and os.path.isdir(output_dir):
        shutil.rmtree(output_dir)
        logging.info(f"Removed directory for series selection: {output_dir}")
    else:
        logging.info(f"Directory for series selection does not exist: {output_dir}")

def list_remote_items_on_oscar(sftp, remote_path):
    """Recursively count and collect all files/dirs inside remote_path."""
    number_of_items = 0
    def recurse(path):
        nonlocal number_of_items
        for entry in sftp.listdir_attr(path):
            full_path = os.path.join(path, entry.filename).replace("\\", "/")
            if stat.S_ISDIR(entry.st_mode):
                recurse(full_path)
                number_of_items += 1
            else:
                number_of_items += 1

    recurse(remote_path)
    return number_of_items

def remove_previous_output_dir_on_oscar(sftp, remote_path, progress_bar, progress_label): 
    """
    Cleans up any previous directory in 'ToProcess' folder on OSCAR for user's UW NET ID
    """
    items_removed = 0
    num_items = 0
    def recurse(remote_path):    
        nonlocal items_removed
        nonlocal progress_bar
        nonlocal progress_label
        nonlocal num_items
        for item in sftp.listdir_attr(remote_path):
            remote_item = os.path.join(remote_path, item.filename).replace("\\", "/")
            if stat.S_ISDIR(item.st_mode):  # it's a directory
                recurse(remote_item)
                sftp.rmdir(remote_item)
                items_removed += 1
            else:  # it's a file
                sftp.remove(remote_item)
                items_removed += 1
            progress_bar.after(0, progress_bar.step, 1)
            percent = int((items_removed / num_items) * 100)
            progress_label.after(0, progress_label.config, {'text': f"Progress: {percent}%"})

    try:
        dir_exists = stat.S_ISDIR(sftp.stat(remote_path).st_mode)
        if dir_exists:
            num_items = list_remote_items_on_oscar(sftp, remote_path)
            progress_bar["maximum"] = num_items
            recurse(remote_path)
            logging.info(f"Removed directory for uploading to OSCAR: {remote_path}")
        return True
    except FileNotFoundError:
        progress_bar["maximum"] = 0
        progress_label.after(0, progress_label.config, {'text': f"Progress: {100}%"})
        logging.info(f"Directory for uploading to OSCAR does not exist: {remote_path}")
        return False
    
def remove_previous_output_dir_on_oscar_modified(sftp, remote_path, clean_progress_func, clean_label_func): 
    """
    Cleans up any previous directory in 'ToProcess' folder on OSCAR for user's UW NET ID
    """
    items_removed = 0
    num_items = 0
    def recurse(remote_path):    
        nonlocal items_removed
        nonlocal num_items
        for item in sftp.listdir_attr(remote_path):
            remote_item = os.path.join(remote_path, item.filename).replace("\\", "/")
            if stat.S_ISDIR(item.st_mode):  # it's a directory
                recurse(remote_item)
                sftp.rmdir(remote_item)
                items_removed += 1
            else:  # it's a file
                sftp.remove(remote_item)
                items_removed += 1
            clean_progress_func(items_removed, num_items)
            percent = int((items_removed / num_items) * 100)
            clean_label_func(f"Progress: {percent}%")
    try:
        dir_exists = stat.S_ISDIR(sftp.stat(remote_path).st_mode)
        if dir_exists:
            num_items = list_remote_items_on_oscar(sftp, remote_path)
            if num_items == 0:
                clean_progress_func(1, 1)
                clean_label_func(f"Progress: 100%")
                return True
            
            recurse(remote_path)
            logging.info(f"Removed directory for uploading to OSCAR: {remote_path}")
        return True
    except FileNotFoundError:
        clean_progress_func(1, 1)
        clean_label_func(f"Progress: 100%")
        logging.info(f"Directory for uploading to OSCAR does not exist: {remote_path}")
        return False