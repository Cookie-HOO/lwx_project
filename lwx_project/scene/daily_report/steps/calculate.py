import csv
import io
import os.path
import random
import time

import pandas as pd
from lwx_project.scene.daily_report.const import *
from lwx_project.utils.calculator import float2int
from lwx_project.utils.excel import call_excel_macro
from lwx_project.utils.files import copy_file
from lwx_project.utils.time_obj import TimeObj


def get_content(df, x_range, y_range):
    if len(x_range) == 2 and len(y_range) == 2:
        data = df.iloc[x_range[0]:x_range[1], y_range[0]:y_range[1]]
        data.iloc[:, 3] = data.iloc[:, 3].apply(lambda x: str(float2int(x)) if not pd.isna(x) else '')
        return data
    return df


def get_cheer_up_text():
    with open(CHEER_UP_TEXT_PATH) as f:
        all_cheer_up_text = f.readlines()
    text_cheer_up = random.choice(all_cheer_up_text).strip("\n")
    today = TimeObj()
    return TEXT_CHEER_UP.format(text_cheer_up=text_cheer_up, season_char=today.season_in_char, month_num=today.month)


def main():
    # 1. 执行指定宏进行填充和排序
    for macro in EXCEL_MARCOS:
        call_excel_macro(excel_path=DAILY_REPORT_TEMPLATE_PATH, macro_name=macro)

    # 2. 获取指定内容生成文本
    df = pd.read_excel(DAILY_REPORT_TEMPLATE_PATH, header=None)
    data = get_content(df, x_range=(6, 19), y_range=(0, 5))
    time_stamp = time.time()
    text_result_path = os.path.join(DATA_RESULT_PATH, f"{time_stamp}_msg.txt")
    string_buf = io.StringIO()
    data.to_csv(string_buf, header=False, index=False, sep=" ", quoting=csv.QUOTE_NONE, escapechar=' ')
    text = string_buf.getvalue().replace("\r\n", "\n") + get_cheer_up_text()
    with open(text_result_path, "w", encoding="utf-8") as f:
        f.write(text)
    # 3. 生成图片待定，将最终的3-13个（1开始）的sheet独立生成一个新的xlsx
    copy_file(DAILY_REPORT_TEMPLATE_PATH, os.path.join(DATA_RESULT_PATH, f"{time_stamp}_每日报表汇总.xlsm"))
    # save_sheet_for_excel(DAILY_REPORT_TEMPLATE_PATH)
    # get_picture(DAILY_REPORT_TEMPLATE_PATH, 1)
    # df_all = pd.read_excel(DAILY_REPORT_TEMPLATE_PATH, header=None, sheet_name=list(range(3,14)))
    # print()


if __name__ == '__main__':
    main()
