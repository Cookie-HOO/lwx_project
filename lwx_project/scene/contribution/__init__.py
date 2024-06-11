import shutil

import pandas as pd

from lwx_project.scene.contribution.const import *
from lwx_project.utils.files import copy_file

from lwx_project.scene.contribution.steps import incremental_contribution, stock_contribution, final_contribution


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

    # 3. 读取文件
    df = pd.read_excel(CONTRIBUTION_PATH, skiprows=1)
    df.columns = [i.replace("\n", "") for i in df.columns]
    df.drop(df.index[-1], inplace=True)

    # 4. 计算增量贡献率
    df = incremental_contribution.main(df)

    # 5. 计算存量贡献率
    df = stock_contribution.main(df)

    # 6. 汇总贡献率
    alpha = None
    df = final_contribution.main(df, alpha)
    return df


def main_with_args(df, alpha):
    df.columns = [i.replace("\n", "") for i in df.columns]
    # df.drop(df.index[-1], inplace=True)
    # 1. 计算增量贡献率
    df = incremental_contribution.main(df)

    # 2. 计算存量贡献率
    df = stock_contribution.main(df)

    # 3. 汇总贡献率
    df = final_contribution.main(df, alpha)

    return df


if __name__ == '__main__':
    main()