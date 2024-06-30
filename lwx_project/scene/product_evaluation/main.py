import shutil

from lwx_project.scene.product_evaluation.const import *
from lwx_project.scene.product_evaluation.steps import data_preprocess, get_text, get_value, split_sheet
from lwx_project.utils.file import copy_file


def before_run():
    # 1. 创建路径
    shutil.rmtree(DATA_TMP_PATH, ignore_errors=True)
    os.makedirs(DATA_TMP_PATH, exist_ok=True)
    os.makedirs(DATA_RESULT_PATH, exist_ok=True)

    # 2. 拷贝关键文件到tmp路径
    for file in os.listdir(DATA_IMPORTANT_PATH):
        if not file.startswith("~") and (file.endswith("xlsx") or file.endswith("xlsm")):
            old_path = os.path.join(DATA_IMPORTANT_PATH, file)
            new_path = os.path.join(DATA_TMP_PATH, file)
            copy_file(old_path, new_path)


def main():
    before_run()

    # 步骤一：数据预处理
    df = data_preprocess.main()

    # 步骤二：生成评估文本
    df_text = get_text.main(df)

    # 步骤三：获取数据
    df_value = get_value.main(df)

    # 步骤四：拆分excel
    split_sheet.main(df_text, df_value)


if __name__ == '__main__':
    main()
