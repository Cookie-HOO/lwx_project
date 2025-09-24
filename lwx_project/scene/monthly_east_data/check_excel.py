"""
1. 区分三个文件
    如果important没有那两个配置文件，那么必须上传，如果有也可以不上传
"""
import os

import pandas as pd

from lwx_project.scene.monthly_east_data.const import NAME_FILE_PATH, NAME_CODE_FILE_PATH
from lwx_project.utils.file import copy_file


def check_excels(file_path_list) -> (bool, str, dict):
    """校验后返回三个文件的路径
    1. 核心团险数据：上传的文件中必须有
    2. 名称：如果important没有，那么必须上传
    3. 名称代码映射：如果important没有，那么必须上传
    校验后，一定会返回这三个文件的路径
    如果后两个文件不在important路径中，那么必须上传，上传后会复制到important路径中
    """
    # 1. 个数校验，不能超过3个文件
    if len(file_path_list) > 3 or len(file_path_list) == 0:
        return False, "最多支持3个文件：核心团险数据、名称、名称代码映射", {}

    need_name_table = not os.path.exists(NAME_FILE_PATH)
    need_name_code_table = not os.path.exists(NAME_CODE_FILE_PATH)

    # 2. 根据列数判断类型，总共三类
    core_tuanxian_table = []
    name_file = []
    name_code_file = []
    for file_path in file_path_list:
        col_length = len(pd.read_excel(file_path).columns)
        if col_length == 1:
            name_file.append(file_path)
        elif col_length == 2:
            name_code_file.append(file_path)
        else:
            core_tuanxian_table.append(file_path)
    if need_name_code_table and not name_code_file:
        return False, f"需要名称代码表，但是没有上传\n\n请上传只有一列没有表头的其他关联方名称表", {}
    if need_name_table and not name_file:
        return False, f"需要名称表，但是没有上传\n\n请上传只有两列没有表头的其他关联方名称代码映射表，第一列是名称，第二列是代码", {}
    if not core_tuanxian_table:
        return False, "没有上传核心团险表", {}

    # 3. 把上传的配置表复制到important路径下
    if name_file:
        copy_file(name_file[0], NAME_FILE_PATH)
    if name_code_file:
        copy_file(name_code_file[0], NAME_CODE_FILE_PATH)
    return True, "", {
        "核心团险数据": core_tuanxian_table[0],
        "名称": NAME_FILE_PATH,
        "名称代码映射": NAME_CODE_FILE_PATH,
    }

