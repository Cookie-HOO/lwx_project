
"""
1. 删除sheet：
    上月底表，上月底6807

2. 覆盖sheet
    业绩报表
    同比表

3. 修改sheet名
    当月底表 -> 上月底表
    当月底6807 -> 上月底6807
"""
import os

from lwx_project.scene.monthly_profit.utils import build_profit_result_path_from_year_month, \
    build_achieve_result_path, build_detail_result_path, build_achieve_result_png_path, build_result_zip_path
from lwx_project.utils.biz import sheet_capture2
from lwx_project.utils.excel_style import ExcelStyleValue
from lwx_project.utils.file import make_zip_by_files, copy_file
from lwx_project.utils.year_month_obj import YearMonth


def copy_and_fill_excel(year_month: YearMonth, path_dict):
    """
    "当月底表": cur_month_path,
    "当月6807": cur_6807_path,
    "业绩表": biz_report_path,
    "同比表": tongbi_path,
    "上月模板": target_last_template_path,  # 在important路径中的上月模板
    """
    path = path_dict.get("模板")  # important路径中的本月模板
    cur_month_path = path_dict.get("当月底表")
    cur_6807_path = path_dict.get("当月6807")
    biz_profit_path = path_dict.get("业绩表")
    tongbi_path = path_dict.get("同比表")


    # 1. 处理上月表和当月表
    #   如果是一月，清空sheet: 上月底表，上月底6807，保留sheet，只是清空内容
    #   如果不是，删除上月，将当月重命名为上月

    # 删除path 的 sheet: 上月底表，上月底6807
    # 将{当月底} sheet 重命名为{上月底} sheet
    # 将{当月底6807} sheet 重命名为{上月底6807} sheet
    esv = ExcelStyleValue(path, run_mute=True)
    esv.switch_sheet("上月底表").sheet_copy_from_other_excel(other_excel_sheet_name="当月底表")
    esv.switch_sheet("上月底6807").sheet_copy_from_other_excel(other_excel_sheet_name="当月底6807")

    if year_month.month == 1:
        # 清空path 的 sheet: 上月底表，上月底6807
        esv.switch_sheet("上月底表").clear()
        esv.switch_sheet("上月底6807").clear()

    # 2. 拷贝当月表: 将上传的当月内容上传过去
    esv.switch_sheet("当月底表").sheet_copy_from_other_excel(cur_month_path)
    esv.switch_sheet("当月底6807").sheet_copy_from_other_excel(cur_6807_path)


    # 3. 覆盖剩下的两张表
    esv.switch_sheet("业绩报表").sheet_copy_from_other_excel(biz_profit_path)
    esv.switch_sheet("同比表").sheet_copy_from_other_excel(tongbi_path)
    return esv

def adjust_result(esv: ExcelStyleValue, year_month: YearMonth):
    """
    做一些文字的调整
    1. 达成表的处理
        - 文字
            截至 上个月的月底，九月做，做八月的，写八月底
            注的第二行：
                截至8月底
                以 xxx 为准
        - 排序
            3-25行的数字，对F列（计划达成率）排序，降序
        - 修改字体
            超过100%的红底黄字
            超过序时进度的黄底黑字
            其他：绿底黑字
    2. 明细表的处理
        - 文字
            标题：截至 上个月的月底，九月做，做八月的，写八月底
            挑选：较上月小于-50的行，补充：利润较低，主要原因
                1. 当月保费（不含税）：如果这一列比，当月主要支出里面最大的小，就说：保费收入较低
                2. 当月主要支出中，找到所有超过均值的项，说该项较高
    """
    # 1. 处理 达成表
    # 1.1 改文字
    esv.switch_sheet("达成表")
    esv.update_text_shape({"\s*2025年团险利润计划达成报表.*": f"2025年团险利润计划达成报表\n（截至{year_month.month}月底）"})
    text = f"""注：1.表格中标红部分为达成率超100%的分公司，标橘黄部分为达成超序时进度的分公司。 
2.利润为截至{year_month.month}月底数据，分公司团险部分管总及经理以{year_month.month}月{year_month.max_day_of_month}日实际在岗为准。"""
    esv.set_cell((27, 1), text)

    # 1.2 排序：对F3到F25排序（降序）
    esv.range_sort(6, "A3:I25", desc=True)
    # 1.2 超过1的设置为红底黄字
    values = esv.get_cell("F3:F25")  # 排好序了（倒排）
    bigger_than_1_index = [i for i, v in enumerate(values) if v >= 1]
    max_row_num_of_1 = max(bigger_than_1_index) + 3
    esv.set_style(f"A3:I{max_row_num_of_1}", bg_color=(192, 0, 0), font_color=(255, 255, 0), bold=True)

    # 1.3 超过序时进度的黄底黑字
    min_row_num = max_row_num_of_1 + 1
    bigger_than_1_index = [i for i, v in enumerate(values) if v >= year_month.month/12]
    max_row_num_of_should = max(bigger_than_1_index) + 3
    esv.set_style(f"A{min_row_num}:I{max_row_num_of_should}", bg_color=(255, 192, 0), font_color=(0, 0, 0), bold=True)

    # 1.4 其他都是 绿底黑字
    min_row_num = max_row_num_of_should + 1
    max_all = 25
    esv.set_style(f"A{min_row_num}:I{max_all}", bg_color=(226, 239, 218), font_color=(0, 0, 0), bold=True)

    # 2. 处理 明细表
    # 2.1 改文字
    esv.switch_sheet("明细表")
    esv.set_cell((1,1), f"2025年团险利润计划达成报表（截至{year_month.month}月底）")

    # 2.2 添加理由
    condition_col_num = 8  # 对第8列的值进行检查
    update_col_num = 17  # 更新17列的值
    start_row_num = 4
    end_row_num = 26

    # 需要补充原因
    threshold = -50  # 小于这个值就需要标注原因
    col_up = 10  # 当月保费（不含税）
    col_down_start = 11
    col_down_end = 15
    row_num_of_down_name = 3

    for row_num_pointer in range(start_row_num, end_row_num+1):
        v = esv.get_cell((row_num_pointer, condition_col_num))
        if v < threshold:  # 需要补充原因：第17列
            # 1. 找到支出超过均值的名称
            down_amount_list = [esv.get_cell((row_num_pointer, col_down)) for col_down in range(col_down_start, col_down_end+1)]
            down_name_list = [esv.get_cell((row_num_of_down_name, col_down)) for col_down in range(col_down_start, col_down_end+1)]

            avg = sum(down_amount_list) / len(down_amount_list)
            names = [name for num, name in zip(down_amount_list, down_name_list) if num > avg]
            reason1 = "、".join(names) + "较高"

            # 2. 比较收入是否比最大项要小
            up_amount = esv.get_cell((row_num_pointer, col_up))
            reason2 = ""
            if up_amount < max(down_amount_list):
                reason2 = "保费收入较低"

            # 3. 合并
            reason = reason1 + "，" + reason2
            esv.set_cell((row_num_pointer, update_col_num), reason)
        else:
            esv.set_cell((row_num_pointer, update_col_num), None)

    path = esv.excel_path
    esv.save()

    # 新建 达成表 和 明细表的单独excel
    copy_file(path, build_achieve_result_path(year_month))
    copy_file(path, build_detail_result_path(year_month))

    ExcelStyleValue(build_achieve_result_path(year_month), run_mute=True).batch_delete_sheet_except(["达成表"]).save()
    ExcelStyleValue(build_detail_result_path(year_month), run_mute=True).batch_delete_sheet_except(["明细表"]).save()


def result_sheet_capture(year_month: YearMonth):
    path_dacheng_png_path = build_achieve_result_png_path(year_month)

    target_path = build_profit_result_path_from_year_month(year_month)
    sheet_capture2(target_path, "达成表", path_dacheng_png_path, run_mute=True)

def make_result_zip(year_month: YearMonth):
    """两个excel 和 一个截图"""
    excel1 = build_detail_result_path(year_month)
    excel2 = build_achieve_result_path(year_month)
    png1 = build_achieve_result_png_path(year_month)
    path = make_zip_by_files([excel1, excel2, png1], build_result_zip_path(year_month))
    os.remove(excel1)
    os.remove(excel2)
    os.remove(png1)
