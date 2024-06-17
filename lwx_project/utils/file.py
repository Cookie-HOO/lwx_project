import os
import shutil


def copy_file(old_path, new_path, overwrite_if_exists=True):
    if os.path.isdir(old_path) or os.path.isdir(new_path):
        return
    if overwrite_if_exists:
        if os.path.exists(new_path):
            print(f"PATH: {new_path} exists, deleting...")
            os.remove(new_path)
    os.makedirs(os.path.dirname(new_path), exist_ok=True)
    shutil.copyfile(old_path, new_path)


def get_file_name_without_extension(file_name):
    return os.path.splitext(os.path.basename(file_name))[0]