import collections
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


def copy_file(old_path, new_path, overwrite_if_exists=True):
    if not old_path or not new_path:
        return
    if os.path.isdir(old_path) or os.path.isdir(new_path):
        return
    if old_path == new_path:
        return
    if overwrite_if_exists:
        if os.path.exists(new_path):
            print(f"PATH: {new_path} exists, deleting...")
            os.remove(new_path)
    os.makedirs(os.path.dirname(new_path), exist_ok=True)
    shutil.copyfile(old_path, new_path)


def make_zip(source_directory, output_filename):
    """将一个目录下的素有文件和子目录打包"""
    shutil.make_archive(output_filename, 'zip', source_directory)

def make_zip_by_files(source_files, output_zip_path):
    import zipfile

    """
    将指定的多个文件（或目录）打包成一个 ZIP 压缩文件

    :param source_files: 要打包的文件/目录路径列表，如 ['a.txt', 'folder/', 'b.xlsx']
    :param output_zip_path: 输出的 ZIP 文件路径，如 'output.zip'
    """
    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for item in source_files:
            if os.path.isfile(item):
                # 添加单个文件，保留原始文件名
                zipf.write(item, arcname=os.path.basename(item))
            elif os.path.isdir(item):
                # 递归添加整个目录
                for root, dirs, files in os.walk(item):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # 计算在 ZIP 中的相对路径（保留目录结构）
                        arcname = os.path.relpath(file_path, os.path.dirname(item))
                        zipf.write(file_path, arcname=arcname)
            else:
                raise FileNotFoundError(f"文件或目录不存在: {item}")

def get_file_name_without_extension(file_path):
    return os.path.splitext(os.path.basename(file_path))[0]


def get_file_name_with_extension(file_path):
    return os.path.basename(file_path)


FileDetail = collections.namedtuple(
    "FileDetail", ["path", "size_format", "size_in_bytes", "updated_at", "name_with_extension", "name_without_extension"]
)


def get_file_detail(file_path: str) -> FileDetail:
    """
    获取文件的详细信息。

    :param file_path: 文件的完整路径
    :return: FileDetail 对象，包含以下字段：
        - path: 文件的完整路径
        - size: 文件大小（字节）
        - updated_at: 文件最后修改时间（格式化为字符串）
        - name_with_extension: 文件名（带扩展名）
        - name_without_extension: 文件名（不带扩展名）
    """
    # 确保路径存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件未找到: {file_path}")

    # 使用 pathlib 处理路径
    file_path_obj = Path(file_path)

    # 获取文件大小（字节）
    size_in_bytes = file_path_obj.stat().st_size

    # 获取文件最后修改时间
    updated_timestamp = file_path_obj.stat().st_mtime
    updated_at = datetime.fromtimestamp(updated_timestamp).strftime("%Y-%m-%d %H:%M:%S")

    # 返回 FileDetail 对象
    return FileDetail(
        path=str(file_path_obj.resolve()),  # 文件的绝对路径
        size_in_bytes=size_in_bytes,
        size_format=file_size_format(size_in_bytes),
        updated_at=updated_at,
        name_with_extension=file_path_obj.name,
        name_without_extension=file_path_obj.stem,
    )


def open_file_or_folder(file_or_folder_path):
    """模拟双击打开的操作
    win：File Explorer
    mac: finder
    """
    if os.path.exists(file_or_folder_path):
        if os.name == 'nt':  # 对于Windows
            os.startfile(file_or_folder_path)
        elif os.name == 'posix':  # 对于macOS和Linux
            subprocess.call(['open', file_or_folder_path])

    # if os.path.exists(file_or_folder_path):
    #     webbrowser.open(file_or_folder_path)


def file_size_format(size_in_bytes: int) -> str:
    """
    将文件大小从字节转换为易读的字符串表示形式。

    :param size_in_bytes: 文件大小（字节）
    :return: 易读的文件大小字符串（例如 "1.2 KB", "3.5 MB"）
    """
    # 定义单位列表
    units = ["B", "KB", "MB", "GB", "TB"]

    # 初始化变量
    size = float(size_in_bytes)
    unit_index = 0

    # 逐步转换到更大的单位
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    # 格式化输出，保留两位小数
    return f"{size:.2f} {units[unit_index]}"
