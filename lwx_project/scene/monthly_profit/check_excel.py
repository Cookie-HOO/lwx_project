"""
每月做一次的利润表
输入：四个文件的path
输出：返回四个文件的路径

输入
	1. 当月底表.xlsx
	2. 当月6807.xlsx
	3. 业绩报表
	4. 同比表
通过检查列，自动判断
	1和2不好区分：B6 = 产品段=6807  就是6807

检查
	1. 两个当月的
		从B7到AA7的值和顺序
		B9是数字，B8是空，B10是数字，C9是数字
"""
import os
import typing

from lwx_project.scene.monthly_profit.const import TEMPLATE_PATH
from lwx_project.scene.monthly_profit.utils import build_profit_result_path_from_year_month
from lwx_project.utils.excel_style import ExcelStyleValue
from lwx_project.utils.file import copy_file
from lwx_project.utils.high_performance import FastExcelReader
from lwx_project.utils.year_month_obj import YearMonth

ORDER = "合计	总公司	分公司小计	北京分公司	河北分公司	山西分公司	辽宁分公司	江苏分公司	宁波分公司	浙江分公司	福建分公司	山东分公司	河南分公司	湖北分公司	湖南分公司	四川分公司	陕西分公司	安徽分公司	苏州分公司	广东分公司	上海分公司	厦门分公司	黑龙江分公司	江西分公司	广西分公司	重庆分公司"


def value_and_assign_check(check_name, reader: FastExcelReader, row_num, col_num, target_value, before_assign_value=None) -> typing.Optional[bool]:
    """返回值：None没命中， Bool是否报错"""
    v = reader.get_cell_value(row_num, col_num)
    if isinstance(v, str) and v.strip() == target_value.strip():
        if before_assign_value is not None:
            raise ValueError("检查：{}时，多个表命中条件：row: {}, col: {}是{}".format(check_name, row_num, col_num, target_value))
        return True
    return None

def row_check(reader):
    """对当月的excel的行进行校验"""
    order = ORDER.split("\t")
    row_num = 7
    col_num_pointer = 2

    # 需要检查分公司的顺序
    for o in order:
        if not reader.check_cell_value(row_num, col_num_pointer, o):
            return "校验分公司顺序不对：row_num {}，col_num {} 不是预期的 {}".format(row_num, col_num_pointer, o)
        col_num_pointer += 1
    # 需要检查上下左是否都是空 合计 是 row_num, 2
    left_check = reader.check_cell_value(row_num, 1, None)
    # up_check = reader.check_cell_value(row_num - 1, 2, None)
    down_check = reader.check_cell_value(row_num + 1, 2, None)
    if not (left_check and down_check):
        return "'合计'的下左存在值，会导致公式计算错误"

    # 需要检查 A9 一、营业收入  A53：八、综合收益总额 A54 是空
    check1 = reader.check_cell_value(9, 1, "一、营业收入")
    check2 = reader.check_cell_value(53, 1, "八、综合收益总额")
    check3 = reader.check_cell_value(54, 1, None)
    if not (check1 and check2 and check3):
        return "当月表的校验：A8、A53、A54的校验失败"
    return ""


def check_excel(year_month: YearMonth, paths):
    cur_month_path = None
    cur_6807_path = None
    biz_report_path = None
    tongbi_path = None
    upload_last_month_path = None


    target_last_year_month_obj = year_month.sub_one_month()

    if len(paths) not in [4, 5]:
        return "仅接受上传四个文件：当月底表、当月6807表、业绩报表、同比表，或再增加一个上个月做好的表", None
    paths_copy = paths[:]

    # 1. 校验上传的所有文件
    while paths_copy:
        path = paths_copy.pop()
        need_check_fengongsi = False
        with FastExcelReader(path) as reader:
            try:
                # 判断当月6807
                if value_and_assign_check("当月6801表", reader, 6, 2, "产品段=6807", cur_6807_path):
                    cur_6807_path = path
                    need_check_fengongsi = True
                # 判断当月底表
                elif value_and_assign_check("当月底表", reader, 7, 2, "合计", cur_month_path):
                    cur_month_path = path
                    need_check_fengongsi = True
                # 判断业绩报表
                elif value_and_assign_check("业绩报表", reader, 3,1, "分公司", biz_report_path):
                    biz_report_path = path
                    # 业绩报表额外检查日期
                    v = reader.get_cell_value(2, 1)
                    biz_profit_report_date = YearMonth.new_from_str(v)
                    if biz_profit_report_date != year_month:
                        return f"上传的业绩报表的日期是：{biz_profit_report_date.str_with_dash}, 目标日期是: {year_month.str_with_dash}", None


                # 判断同比表
                elif value_and_assign_check("同比表", reader, 2,1, "机构", tongbi_path):
                    tongbi_path = path

                # 是上个月做好的表
                else:
                    try:
                        with FastExcelReader(path, sheet_name="业绩报表") as last_month_reader:
                            if year_month.month == 1:
                                return "目标是1月，不能上传上月的模板", None
                            if upload_last_month_path is not None:
                                return "上月模板表重复", None
                            upload_last_month_path = path
                            cell_value = last_month_reader.get_cell_value(2, 1)
                            upload_last_year_month_obj = YearMonth.new_from_str(cell_value)
                            if target_last_year_month_obj != upload_last_year_month_obj:
                                return f"上传的上月模板是: {upload_last_year_month_obj.str_with_dash}而目标年月是{year_month.str_with_dash}, 无法计算目标年月", None
                    except ValueError:
                        pass
                    return f"上传无法解析的表: {path}", None
            except ValueError as e:
                return str(e), None

            # 对于当月表来说，需要进行额外检查
            if need_check_fengongsi:
                err_msg = row_check(reader)
                if err_msg:
                    return err_msg, None

    # 2. 校验所需要的上月模板是否在目标路径下
    target_last_template_path = build_profit_result_path_from_year_month(target_last_year_month_obj)
    target_template_path = build_profit_result_path_from_year_month(year_month)

    if upload_last_month_path:  # 只要上传了模板文件，就会覆盖基础模板文件
        copy_file(upload_last_month_path, TEMPLATE_PATH)

    # 如果不是1月，且找不到上月的，报错
    if year_month.month != 1:
        # 如果上传了上月的模板，会覆盖上月
        if upload_last_month_path:
            copy_file(upload_last_month_path, target_last_template_path)

        if not os.path.exists(target_last_template_path):
            return f"目标年月是{year_month.str_with_dash}, 缺少上月计算结果，请上传", None

    # 从模板拷贝：需要携带宏，不能用其他的文件
    copy_file(TEMPLATE_PATH, target_template_path)

    # 3. 如果上传了模板，需要把内容拷贝到自己的模板中
    if upload_last_month_path:
        esv = ExcelStyleValue(target_template_path)
        esv\
            .switch_sheet("当月底表").sheet_copy_from_other_excel(upload_last_month_path, "当月底表")\
            .switch_sheet("当月底6807").sheet_copy_from_other_excel(upload_last_month_path, "当月底6807")\
            .save()
    # 3. 如果上传了上月，需要把两个上月的sheet，上月底表、上月
    return "", {
        "当月底表": cur_month_path,
        "当月6807": cur_6807_path,
        "业绩表": biz_report_path,
        "同比表": tongbi_path,
        "模板": target_template_path,  # 在important路径中的这个月的文件
    }


