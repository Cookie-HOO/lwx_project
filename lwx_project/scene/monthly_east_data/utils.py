import os

import pandas as pd

from lwx_project.scene.monthly_east_data.const import TEMPLATE_FILE_NAME_PREFIX, TEMPLATE_FILE_NAME_SUFFIX, \
    IMPORTANT_PATH
from lwx_project.utils.year_month_obj import YearMonth


def __build_connection_dict(df):
    """
    从DataFrame构建字典，要求：
    1. 跳过key为NaN的行
    2. 跳过value为空（NaN或空字符串）的行
    3. 同一个key只能对应一个非空value，否则报错
    """
    connection_name_code = {}

    for idx, row in df.iterrows():
        # 处理 key
        key_raw = row[df.columns[0]]
        if pd.isna(key_raw):
            continue  # 跳过 key 为 NaN 的行
        key = str(key_raw)

        # 处理 value
        value_raw = row[df.columns[1]]
        if pd.isna(value_raw):
            continue  # 跳过 value 为 NaN 的行

        value_str = str(value_raw).strip()
        if not value_str:  # 跳过空字符串
            continue

        # 检查是否已经存在该key
        if key in connection_name_code:
            # 如果已存在的值与当前值不同，则报错
            if connection_name_code[key] != value_str:
                raise ValueError(
                    f"Key '{key}' 对应多个不同的值: "
                    f"'{connection_name_code[key]}' 和 '{value_str}' "
                    f"(行索引: {idx})"
                )
        else:
            # 第一次遇到这个key，添加到字典
            connection_name_code[key] = value_str

    return connection_name_code


def get_name_code_map(connection_name_code_path) -> dict:
    """根据名称代码的路径，返回名称代码映射"""
    connection_name_code_df = pd.read_excel(connection_name_code_path, header=None)
    # 创建映射字典，确保键是字符串类型
    connection_name_code = __build_connection_dict(connection_name_code_df)
    return connection_name_code


def get_name(connection_name_path) -> list:
    """根据名称的路径，返回名称的列表"""
    connection_name_df = pd.read_excel(connection_name_path, header=None)
    connection_name = [str(name) for name in connection_name_df.iloc[:, 0].tolist()]
    return connection_name


def build_east_result_name_from_year_month(year_month: YearMonth) -> str:
    """根据年月，找到生成的模板名称"""
    name = TEMPLATE_FILE_NAME_PREFIX + year_month.str_with_only_number + TEMPLATE_FILE_NAME_SUFFIX
    return name

def build_east_result_path_from_year_month(year_month: YearMonth) -> str:
    """根据年月，找到生成的模板路径"""
    path = os.path.join(IMPORTANT_PATH, build_east_result_name_from_year_month(year_month))
    return path