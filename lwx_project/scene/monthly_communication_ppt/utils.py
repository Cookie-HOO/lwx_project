import os

from lwx_project.scene.monthly_communication_ppt.const import PPT_FILE_NAME_TEMPLATE, IMPORTANT_PATH, \
    EXCEL_FILE_NAME_TEMPLATE
from lwx_project.utils.year_month_obj import YearMonth


def make_ppt_file_name(year_month_obj: YearMonth) -> str:
    month_range = "1"
    if year_month_obj.month != 1:
        month_range = f"1-{year_month_obj.month}"
    ppt_file_name = PPT_FILE_NAME_TEMPLATE.format(year=year_month_obj.year, month_range=month_range)
    return ppt_file_name

def make_ppt_file_path(year_month_obj: YearMonth) -> str:
    return os.path.join(IMPORTANT_PATH, make_ppt_file_name(year_month_obj=year_month_obj))

def make_excel_file_name(year_month_obj: YearMonth) -> str:
    month_range = "1"
    if year_month_obj.month != 1:
        month_range = f"1-{year_month_obj.month}"
    ppt_file_name = EXCEL_FILE_NAME_TEMPLATE.format(year=year_month_obj.year, month_range=month_range)
    return ppt_file_name

def make_excel_file_path(year_month_obj: YearMonth) -> str:
    return os.path.join(IMPORTANT_PATH, make_excel_file_name(year_month_obj=year_month_obj))

def make_month_range(year_month_obj: YearMonth):
    month_range = "1"
    if year_month_obj.month != 1:
        month_range = f"1-{year_month_obj.month}"
    return month_range
