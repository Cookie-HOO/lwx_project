import os

from lwx_project.scene.monthly_profit.check_excel import check_excel
from lwx_project.scene.monthly_profit.const import IMPORTANT_PATH, DATA_PATH
from lwx_project.scene.monthly_profit.fill_excel import copy_and_fill_excel, result_sheet_capture, adjust_result, \
    make_result_zip
from lwx_project.utils.year_month_obj import YearMonth


def check_and_run(year_month: YearMonth, paths: list) -> str:
    # 1. check
    err_msg, path_dict = check_excel(year_month, paths)
    if err_msg:
        return err_msg
    try:
        # 2. run
        esv = copy_and_fill_excel(year_month, path_dict)
        # 3. adjust
        adjust_result(esv, year_month)
        # 4. sheet capture
        result_sheet_capture(year_month)
        # 4. zip
        make_result_zip(year_month)
    except Exception as e:
        return str(e)
    return ""

if __name__ == '__main__':
    year_month_ = YearMonth(year=2025, month=9)
    paths_ = [
        os.path.join(DATA_PATH, "当月底6807.xlsx"),
        os.path.join(DATA_PATH, "当月底表.xlsx"),
        os.path.join(DATA_PATH, "同比表.xlsx"),
        os.path.join(DATA_PATH, "业绩报表.xlsx"),
    ]
    check_and_run(year_month_, paths_)
