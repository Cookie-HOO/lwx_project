import os

from lwx_project.scene.monthly_profit.const import IMPORTANT_PATH, TEMPLATE_FILE_NAME_PREFIX, TEMPLATE_FILE_NAME_SUFFIX
from lwx_project.utils.year_month_obj import YearMonth


def build_profit_result_name_from_year_month(year_month: YearMonth) -> str:
    """根据年月，找到生成的模板名称"""
    name = TEMPLATE_FILE_NAME_PREFIX + year_month.str_with_only_number + TEMPLATE_FILE_NAME_SUFFIX
    return name


def build_profit_result_path_from_year_month(year_month: YearMonth) -> str:
    """根据年月，找到生成的模板路径"""
    path = os.path.join(IMPORTANT_PATH, build_profit_result_name_from_year_month(year_month))
    return path

def build_achieve_result_path(year_month: YearMonth) -> str:
    path = os.path.join(IMPORTANT_PATH, f"利润达成表{year_month.str_with_only_number}.xlsx")
    return path


def build_detail_result_path(year_month: YearMonth) -> str:
    path = os.path.join(IMPORTANT_PATH, f"利润达成明细表{year_month.str_with_only_number}.xlsx")
    return path

def build_achieve_result_png_path(year_month: YearMonth) -> str:
    path = os.path.join(IMPORTANT_PATH, "达成表" + year_month.str_with_only_number + ".png")
    return path

def build_result_zip_name(year_month: YearMonth) -> str:
    return "利润达成统计" + year_month.str_with_only_number + ".zip"

def build_result_zip_path(year_month: YearMonth) -> str:
    path = os.path.join(IMPORTANT_PATH, build_result_zip_name(year_month))
    return path
