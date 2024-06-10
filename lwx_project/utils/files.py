import os
import shutil


def copy_file(old_path, new_path, overwrite_if_exists=True):
    if overwrite_if_exists:
        if os.path.exists(new_path):
            print(f"PATH: {new_path} exists, deleting...")
            os.remove(new_path)
    shutil.copyfile(old_path, new_path)