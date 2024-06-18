import csv
import io
import os.path
import random
import time

import pandas as pd
from lwx_project.scene.daily_report.const import *
from lwx_project.utils.conf import get_txt_conf
from lwx_project.utils.df import get_window_of_df_as_df
from lwx_project.utils.excel import call_excel_macro
from lwx_project.utils.file import copy_file
from lwx_project.utils.time_obj import TimeObj


def get_cheer_up_text() -> (str, dict):
    """生成cheerup的文本模板，和填充的变量
    :return:
    """
    all_motto_text = get_txt_conf(MOTTO_TEXT_PATH, list)
    leader_word_template_text = get_txt_conf(LEADER_WORD_TEMPLATE_PATH, str)
    text_motto = random.choice(all_motto_text)
    today = TimeObj()
    text_variable = dict(motto=text_motto, season_char=today.season_in_char, month_num=today.month, all_motto_text=all_motto_text)
    return leader_word_template_text, text_variable


def main(copy2tmp_path_list=None, run_mute=False):
    # 0. copy宏文件到tmp目录
    copy_file(DAILY_REPORT_SOURCE_TEMPLATE_PATH, DAILY_REPORT_TMP_TEMPLATE_PATH)
    if copy2tmp_path_list:
        for file in copy2tmp_path_list:
            copy_file(file, os.path.join(DATA_TMP_PATH, os.path.basename(file)))

    # 1. 执行指定宏进行填充和排序
    call_excel_macro(excel_path=DAILY_REPORT_TMP_TEMPLATE_PATH, macro_names=EXCEL_MARCOS, run_mute=run_mute)

    # 2. 获取指定内容生成文本
    df = pd.read_excel(DAILY_REPORT_TMP_TEMPLATE_PATH, header=None)
    data = get_window_of_df_as_df(df, x_range=(6, 19), y_range=(0, 5))
    string_buf = io.StringIO()
    data.to_csv(string_buf, header=False, index=False, sep=" ", quoting=csv.QUOTE_NONE, escapechar=' ')
    num_text = string_buf.getvalue().replace("\r\n", "\n")
    leader_word_template_text, leader_word_variables = get_cheer_up_text()
    # 3. 生成图片待定，将最终的3-13个（1开始）的sheet独立生成一个新的xlsx
    copy_file(DAILY_REPORT_TMP_TEMPLATE_PATH, os.path.join(DATA_RESULT_PATH, f"每日报表汇总.xlsm"))
    # save_sheet_for_excel(DAILY_REPORT_TEMPLATE_PATH)
    # get_picture(DAILY_REPORT_TEMPLATE_PATH, 1)
    # df_all = pd.read_excel(DAILY_REPORT_TEMPLATE_PATH, header=None, sheet_name=list(range(3,14)))
    # print()
    return {
        "num_text": num_text,
        "leader_word_variables": leader_word_variables,
    }


if __name__ == '__main__':
    main()
