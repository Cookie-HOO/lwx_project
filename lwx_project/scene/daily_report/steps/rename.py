import os.path
import re
import typing

import pandas as pd

from lwx_project.scene.daily_report.const import *
from lwx_project.utils.file import copy_file
from lwx_project.utils.time_obj import TimeObj


def new_name_time(title, text_parts, old_name, date_equal_buffer, report_date) -> typing.List[str]:
    # 当年 or 当季 or 当月 or 当日
    new_name_time_list = []
    if len(text_parts) > 0:
        time_str = text_parts[0]
        start_end_time = time_str.lstrip("日期：").split("--")
        if len(start_end_time) == 2:
            start_time, end_time = start_end_time
            start_time = TimeObj(raw_time=start_time, equal_buffer=date_equal_buffer, base_time=report_date)
            end_time = TimeObj(raw_time=end_time, equal_buffer=date_equal_buffer, base_time=report_date)
            if start_time == end_time:
                new_name_time_list.append("当日")
            if start_time.is_first_day_of_base_month:
                new_name_time_list.append("当月")
            if start_time.is_first_day_of_base_season:
                new_name_time_list.append("当季")
            if start_time.is_first_day_of_base_year:
                new_name_time_list.append("当年")

    return new_name_time_list


def new_name_index(title, text_parts):
    if title == "分行代理保险产品分险种销售情况统计表":
        return "26"
    elif title == "网点经营情况统计表":
        return "23"
    return ""


def new_name_position(title, text_parts):
    # 公司 or 全 or 农 or 活动率
    if title == "分行代理保险产品分险种销售情况统计表":
        return "全"
    elif title == "网点经营情况统计表":
        return "活动率"
    elif len(text_parts) >= 2:
        pos_str = text_parts[1]
        if pos_str.startswith("公司："):
            if pos_str == "公司：('1118')":
                return "农"
            elif pos_str.startswith("公司：("):
                return "全"
        elif pos_str == "机构：总行":
            return "公司"
    return ""


def get_key_text_parts(df):
    """获取一个df的关键文本
    :param df:
    :return:
    """
    text = df.iloc[1, 0]  # 第二行第一个
    res = re.split("\s{3,}", text)
    res = [i.replace(":", "：") for i in res]
    return res


def get_new_name(df, old_name, date_equal_buffer, report_date) -> typing.List[str]:
    title = df.iloc[0, 0]
    key_text_parts = get_key_text_parts(df)
    if len(key_text_parts) >= 2:
        if key_text_parts[1] == '公司：农银人寿保险股份有限公司':
            return [old_name]

    new_name_template = (f"{new_name_index(title, key_text_parts)}"  # 第一部分是index
                         f"{{new_time}}"  # 第二部分是时间
                         f"{new_name_position(title, key_text_parts)}"  # 第三部分是机构｜农 | 公司
                         f".xlsx")

    return [
        new_name_template.format(new_time=new_time) for new_time in new_name_time(title, key_text_parts, old_name, date_equal_buffer, report_date)
    ]


def main(upload_excels_path=None, date_equal_buffer=0, report_date=None):
    """
    :param upload_excels_path: 所有需要重命名的文件
    :param date_equal_buffer: 时间相等的buffer
    :param report_date: 报表日期
    :return:
    """
    report_date = report_date or TimeObj()-1
    name_dict = {}
    excels = upload_excels_path or os.listdir(DATA_PATH)
    for excel in excels:
        if not excel.startswith("~") and excel.endswith(".xlsx"):
            old_excel_path = excel if upload_excels_path else os.path.join(DATA_PATH, excel)
            try:
                df = pd.read_excel(old_excel_path, header=None, engine='openpyxl')
            except Exception as e:
                print(f"error when loads: {old_excel_path}, {e}")
                return
            new_name_list: typing.List[str] = get_new_name(df, excel, date_equal_buffer, report_date)
            for new_name in new_name_list:
                copy_file(old_excel_path, os.path.join(DATA_TMP_PATH, new_name))
                name_dict[new_name] = get_key_text_parts(df)[0]
    return name_dict


if __name__ == '__main__':
    res = main(date_equal_buffer=0)
    print(res)
