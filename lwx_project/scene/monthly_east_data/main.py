import typing

from lwx_project.scene.monthly_east_data.cal_excel import baoxian_order_code_groupby, CalExcelOneInfo
from lwx_project.scene.monthly_east_data.const import *
from lwx_project.scene.monthly_east_data.fill_excel import clear_and_fill_excel
from lwx_project.utils.file import copy_file


def cal_and_merge(upload_file_path_map: dict, target_year: str, omit_baoxian_code_list: list, call_back_after_one: typing.Callable[[CalExcelOneInfo], None] = None):
    """
    upload_file_path_map: dict
        上传的文件路径映射，{"核心团险数据": "", "名称": "", "名称代码映射": ""}
    target_year: str
        目标年份
    omit_baoxian_code_list: list
        忽略的保险代码列表
    """
    path_dict = upload_file_path_map.get("核心团险数据")  # 有序字典
    name_path = upload_file_path_map.get("名称")
    name_code_path = upload_file_path_map.get("名称代码映射")
    for year_month_obj, p in path_dict.items():
        # 1. 计算这个月的汇总数据
        cal_excel_one_info = baoxian_order_code_groupby(
            path=p,
            cur_year_month=year_month_obj,
            omit_baoxian_code_list=omit_baoxian_code_list,
            year=target_year,
            connection_name_path=name_path,
            connection_name_code_path=name_code_path,
        )

        # 2. 在新的文件中先删除，再填充
        target_file_name = TEMPLATE_FILE_NAME_PREFIX + year_month_obj.str_with_only_number + TEMPLATE_FILE_NAME_SUFFIX
        target_file_path = os.path.join(IMPORTANT_PATH, target_file_name)
        # 基于模板复制
        copy_file(TEMPLATE_PATH, target_file_path)
        # 写入
        clear_and_fill_excel(cal_excel_one_info._df_result, target_file_path)

        if call_back_after_one is not None:
            cal_excel_one_info.target_file_name = target_file_name
            cal_excel_one_info.year_month_obj = year_month_obj
            call_back_after_one(cal_excel_one_info)
