import shutil

from lwx_project.scene.daily_report.const import *
from lwx_project.utils.files import copy_file
from lwx_project.scene.daily_report.steps import rename, calculate


def main():
    # 1. 创建路径
    shutil.rmtree(DATA_TMP_PATH, ignore_errors=True)
    os.makedirs(DATA_TMP_PATH, exist_ok=True)
    os.makedirs(DATA_RESULT_PATH, exist_ok=True)

    # 2. 拷贝关键文件到tmp路径
    for file in os.listdir(DATA_IMPORTANT_PATH):
        if not file.startswith("~"):
            old_path = os.path.join(DATA_IMPORTANT_PATH, file)
            new_path = os.path.join(DATA_TMP_PATH, file)
            copy_file(old_path, new_path)

    # 步骤一：rename
    rename.main()

    # 步骤二：calculate
    calculate.main()


if __name__ == '__main__':
    main()

