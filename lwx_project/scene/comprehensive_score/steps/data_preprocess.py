import datetime

from lwx_project.scene.comprehensive_score.const import *
from lwx_project.utils.excel_style import ExcelStyleValue
from lwx_project.utils.time_obj import TimeObj


def main(report_year, report_month):
    """
    1. 处理上个月得分和排名的两列
    2. 处理前三个sheet的title和注释
    :return:
    """
    report_time_obj = TimeObj(datetime.date(year=report_year, month=report_month, day=1))
    # 1. 处理上个月的得分
    score_wrapper = ExcelStyleValue(SCORE_PATH, "汇总", run_mute=True)\
        .copy_col(from_col_num=7, to_col_num=7)\
        .set_col_by_col(from_col=4, to_col=7, start_row_num=5, end_row_num=27) \
        .set_cell((4, 7), "得分")\
        .set_cell((3, 7), f"{report_month-1}月") \
        .set_cell((3, 4), f"{report_month}月") \
        # .save(os.path.join(DATA_TMP_PATH, "new.xlsx"))

    # 2. 处理上个月的排名
    rank_wrapper = score_wrapper\
        .copy_col(from_col_num=9, to_col_num=8) \
        .set_col_by_col(from_col=5, to_col=8, start_row_num=5, end_row_num=27, end_format=float) \
        .set_cell((4, 8), "排名") \
        .merge_cell(left_top=(3, 7), right_bottom=(3, 8))\
        # .save(os.path.join(DATA_TMP_PATH, "new.xlsx"))

    # 3. 处理三个关键sheet的表头和注释
    extra_text = EXTRA_TEMPLATE1.format(month_num=report_time_obj.month, last_day_of_month=report_time_obj.last_day_of_month.month_day_in_char)
    title_text = TITLE_TEMPLATE.format(year_num=report_time_obj.year, month_num=report_time_obj.month)
    rank_wrapper\
        .set_cell((1, 1), title_text)\
        .set_cell((28, 1), extra_text) \
        .switch_sheet("得分") \
        .set_cell((1, 1), title_text) \
        .set_cell((30, 1), extra_text) \
        .set_cell((31, 1), EXTRA_TEMPLATE2) \
        .switch_sheet("详细") \
        .set_cell((1, 1), title_text) \
        .set_cell((30, 1), extra_text)
    return rank_wrapper


if __name__ == '__main__':
    main(2024, 6)