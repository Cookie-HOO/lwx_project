"""
1. 区分三个文件
    如果important没有那两个配置文件，那么必须上传，如果有也可以不上传
"""
import os
from collections import OrderedDict

from lwx_project.scene.monthly_east_data.const import NAME_FILE_PATH, NAME_CODE_FILE_PATH
from lwx_project.utils.biz import core_tuanxian_get_month
from lwx_project.utils.file import copy_file
from lwx_project.utils.high_performance import FastExcelReader


def check_excels(file_path_list) -> (bool, str, dict):
    """校验后返回三个文件的路径
    1. 核心团险数据：上传的文件中必须有
    2. 名称：如果important没有，那么必须上传
    3. 名称代码映射：如果important没有，那么必须上传
    校验后，一定会返回这三个文件的路径
    如果后两个文件不在important路径中，那么必须上传，上传后会复制到important路径中
    """
    # 1. 个数校验，不能超过3个文件
    if len(file_path_list) == 0:
        return False, "必须要上传文件，至少上传一个核心团险表", {}

    need_name_table = not os.path.exists(NAME_FILE_PATH)
    need_name_code_table = not os.path.exists(NAME_CODE_FILE_PATH)

    # 2. 根据列数判断类型，总共三类
    core_tuanxian_table = {}
    name_file = []
    name_code_file = []
    for file_path in file_path_list:
        with FastExcelReader(file_path) as fe:
            col_length = fe.get_excel_column_count(max_col_num=3)
            if col_length == 1:
                name_file.append(file_path)
            elif col_length == 2:
                name_code_file.append(file_path)
            else:
                # 校验必须的列
                required_cols = ["团体客户名称", "承保日期", "日期", "业务性质"]
                check_yes, left = fe.check_excel_row(row_num=1, required_value_list=required_cols)
                if not check_yes:
                    lack_cols = ", ".join(required_cols)
                    return False, f"核心团险表缺少以下列：\n{lack_cols}", {}

                # 获取月份
                year_month= core_tuanxian_get_month(file_path)
                if year_month is None:
                    return False, f"核心团险表的日期格式不正确，应该是 yyyy-mm-dd", {}
                core_tuanxian_table[year_month] = file_path

    # 如果核心团险数据的超过2个，必须连续
    year_month_list = list(core_tuanxian_table.keys())
    year_month_list.sort()
    # 创建有序字典
    core_tuanxian_table_ordered = OrderedDict(
        (year_month, core_tuanxian_table[year_month])
        for year_month in year_month_list
    )

    if len(core_tuanxian_table) > 2:
        for i in range(len(year_month_list) - 1):
            if year_month_list[i].add_one_month() != year_month_list[i + 1]:
                return False, f"核心团险表的月份必须连续，但是发现有不连续的月份：{year_month_list[i].str_with_dash} 和 {year_month_list[i + 1].str_with_dash}", {}

        # 且必须是相同的年份
        if year_month_list[0].year != year_month_list[-1].year:
            return False, f"核心团险表的年份必须相同，但是发现有不相同的年份：{year_month_list[0].year} 和 {year_month_list[-1].year}", {}

    if need_name_code_table and not name_code_file:
        return False, f"需要名称代码表，但是没有上传\n\n请上传只有一列没有表头的其他关联方名称表", {}
    if need_name_table and not name_file:
        return False, f"需要名称表，但是没有上传\n\n请上传只有两列没有表头的其他关联方名称代码映射表，第一列是名称，第二列是代码", {}
    if not core_tuanxian_table:
        return False, "没有上传核心团险表", {}

    # 3. 把上传的配置表复制到important路径下（如果原来有，那么会覆盖）
    if name_file:
        copy_file(name_file[0], NAME_FILE_PATH)
    if name_code_file:
        copy_file(name_code_file[0], NAME_CODE_FILE_PATH)
    return True, "", {
        "核心团险数据": core_tuanxian_table_ordered,
        "名称": NAME_FILE_PATH,
        "名称代码映射": NAME_CODE_FILE_PATH,
    }

