import os
import typing

import pandas as pd

from lwx_project.scene.product_evaluation.const import EXCEL_TEMPLATE_PATH, OFFICER_COMPANY_PATH, DATA_TMP_PATH, \
    OFFICER_COMPANY_FILE_NAME_TEMPLATE, FEE_IN_SEASON_BEFORE
from lwx_project.utils.excel_style import ExcelStyleValue
from lwx_project.utils.file import copy_file
from lwx_project.utils.time_obj import TimeObj


def main(df_text, df_value, officer=None):
    """按人员生成excel，每个excel有特定的公司
    一个人一个excel
    每个excel中有一些sheet
    一个sheet，一个公司
    :param df_text:  生成sheet嘴上面的文字
        实际简称   ｜   评价
    :param df_value: 生成sheet的数据
        ['险种名称', '保险公司', '保费', '险种代码', '保险责任分类', '保险责任子分类', '保险期限', '缴费期间',
               '总笔数', '犹撤保费', '退保保费', '本期实现手续费收入', '产品目录统计', '保险类型', '期数',
               '截止上季度实现保费']
        其中：
            保险公司就是实际简称
            截止上季度实现保费     需要用一个变化的列名字替代
    :param officer:  指定人员，只做这一个人的

    :return:
    """
    # excel-sheet顺序
    # 保险公司	序号	险种名称	2022年产品目录第几期	保费	其中：一、二季度保费	险种代码	保险责任分类	保险责任子分类	保险期限	缴费期间	总笔数	犹撤保费	退保保费	本期实现手续费收入
    # 文件预处理：标题+日期+列处理
    ##  列处理 第六列，第7/13/19 行，是 {其中：一季度保费} 可能变化，可能没有
    today = TimeObj()
    ExcelStyleValue(EXCEL_TEMPLATE_PATH, "模板", run_mute=True)\
        .set_cell((1, 1), f"{today.last_season_char_with_year_num}产品后评价表")\
        .set_cell((2, 1), f"日期：{today.last_season_last_day_num[:4]}0101-{today.last_season_last_day_num}   机构：总行   货币单位：万元   统计渠道：全部")\
        .set_cell((7, 6), FEE_IN_SEASON_BEFORE.get(today.season)) \
        .set_cell((13, 6), FEE_IN_SEASON_BEFORE.get(today.season)) \
        .set_cell((19, 6), FEE_IN_SEASON_BEFORE.get(today.season)) \
        .delete_col(6, today.season == 1) \
        .set_cell((7, 4), f"{today.year}年产品目录第几期") \
        .set_cell((13, 4), f"{today.year}年产品目录第几期") \
        .set_cell((19, 4), f"{today.year}年产品目录第几期") \
        .save()
    officer_company_df = pd.read_csv(OFFICER_COMPANY_PATH)
    """人员、公司"""
    if officer:
        officer_company_df = officer_company_df[officer_company_df["人员"] == officer]
    grouped = officer_company_df.groupby(by="人员", as_index=False).agg(list)
    grouped.apply(lambda row: split_files(row["人员"], row["公司"], df_text, df_value), axis=1)


def split_files(officer: str, company_list: typing.List[str], df_text, df_value):
    """
    :param officer: 张三
    :param company_list:[农银人寿, 泰康人寿...]
    :param df_text: df: 实际简称 和 评价 两列
    :param df_value:[农银人寿, 泰康人寿...]
    :return:
    """

    """
        模板内容（20行，15列）
        1. 列顺序
            保险公司	序号	险种名称	2022年产品目录第几期	保费	其中：一、二季度保费	险种代码	保险责任分类	保险责任子分类	保险期限	缴费期间	总笔数	犹撤保费	退保保费	本期实现手续费收入
        2. 
            第一行: 居中的标题：
                2022年三季度产品后评价表
            第二行：日期是到上一个季度的最后一天，其他固定
                日期：20220101-20220930   机构：总行   货币单位：万元   统计渠道：全部
            第三行：
                【评价】
            第4-6行：是评价的具体内容
                2022年前三季度，xxxx，几款什么产品 结束
                我行代理xxxx
                主要产品情况xxx

            有保费
                第7行：列名
                第8行：有保费的具体数据
                    保险公司要居中，序号要排序（对保费降序）
            第9-11：空行
            团险：可能没有
                第12行：居中的标题
                    团险
                第13行：列名
                第14行：团险的具体数据
            第15-17：空行
            无保费
                第18行：居中的标题
                    只退保无保费
                第19行：列名
                第20行：无保费的具体数据
        """
    # 1. 拷贝一个模板出来
    today = TimeObj()
    new_file_name = OFFICER_COMPANY_FILE_NAME_TEMPLATE.format(officer=officer, last_season_char_with_year_num=today.last_season_char_with_year_num)
    new_file_path = os.path.join(DATA_TMP_PATH, new_file_name)
    copy_file(EXCEL_TEMPLATE_PATH, new_file_path)

    # 2. 根据模板填值
    df_text[['评价1', '评价2', '评价3']] = df_text['评价'].str.split('\n', expand=True)  # 按照\n进行拆分多列  0 1 2
    esv = ExcelStyleValue(new_file_path, "模板", run_mute=True)
    esv\
        .set_cell((1, 1), f"{today.last_season_char_with_year_num}产品后评价表")\
        .set_cell((2, 1), f"日期：{today.last_season_last_day_num[:4]}0101-{today.last_season_last_day_num}   机构：总行   货币单位：万元   统计渠道：全部")\
        .set_cell((3, 1), f"【评价】")\
        .batch_copy_sheet(company_list, append=False, del_old=True)\
        .for_each_sheet(lambda company: esv.set_cell((4, 1), df_text[df_text["实际简称"] == company]["评价1"].item())) \
        .for_each_sheet(lambda company: esv.set_cell((5, 1), df_text[df_text["实际简称"] == company]["评价2"].item())) \
        .for_each_sheet(lambda company: esv.set_cell((6, 1), df_text[df_text["实际简称"] == company]["评价3"].item())) \
        .for_each_sheet(lambda company: esv.set_cell((8, 1), company)) \
        .for_each_sheet(lambda company: esv.set_cell((14, 1), company)) \
        .for_each_sheet(lambda company: esv.set_cell((20, 1), company)) \
        .for_each_sheet(lambda company: product_rows(company, df_value, esv))\
        .save()
    pass


def product_rows(company, df_value, esv):
    df_value = df_value[df_value["保险公司"] == company]
    has_baoixan_fee = df_value[df_value["保险类型"] == "有保费"].sort_values('保费', ascending=False).reset_index()
    tuanxian = df_value[df_value["保险类型"] == "团险"].sort_values('保费', ascending=False).reset_index()
    no_baoixan_fee = df_value[df_value["保险类型"] == "无保费"].sort_values('保费', ascending=False).reset_index()

    has_baoixan_fee["序号"] = has_baoixan_fee.index + 1
    tuanxian["序号"] = tuanxian.index + 1
    no_baoixan_fee["序号"] = no_baoixan_fee.index + 1
    final_list = ['保险公司', '序号', '险种名称', '期数', '保费', '截止上季度实现保费', '险种代码', '保险责任分类',
                  '保险责任子分类', '保险期限', '缴费期间',
                  '总笔数', '犹撤保费', '退保保费', '本期实现手续费收入']
    if TimeObj().season == 1:
        final_list.remove('截止上季度实现保费')
    """
            ['险种名称', '保险公司', '保费', '险种代码', '保险责任分类', '保险责任子分类', '保险期限', '缴费期间',
               '总笔数', '犹撤保费', '退保保费', '本期实现手续费收入', '产品目录统计', '保险类型', '期数',
               '截止上季度实现保费']
               
        # 保险公司	序号	险种名称	2022年产品目录第几期	保费	其中：一、二季度保费	险种代码	保险责任分类	保险责任子分类	保险期限	缴费期间	总笔数	犹撤保费	退保保费	本期实现手续费收入
    """
    # 有保费
    has_baoixan_fee_length = len(has_baoixan_fee)
    has_baoixan_fee_start = 8  # 数据开始
    has_baoixan_fee_end = has_baoixan_fee_start + has_baoixan_fee_length - 1  # 数据结束
    esv\
        .set_cell((6, 1), "", limit=not has_baoixan_fee_length)\
        .copy_row_down(has_baoixan_fee_start, has_baoixan_fee_length-1, set_df=has_baoixan_fee[final_list], limit=has_baoixan_fee_length)\
        .batch_delete_row(7, 11, limit=not has_baoixan_fee_length)\
        .merge_cell((has_baoixan_fee_start, 1), (has_baoixan_fee_end, 1), limit=has_baoixan_fee_length > 1)

    # 团险
    tuanxian_lenth = len(tuanxian)
    tuanxian_start = has_baoixan_fee_start + has_baoixan_fee_length - 1 + 3 + 3 if has_baoixan_fee_length else 9
    tuanxian_end = tuanxian_start + tuanxian_lenth - 1
    esv\
        .copy_row_down(tuanxian_start, tuanxian_lenth-1, set_df=tuanxian[final_list], limit=tuanxian_lenth)\
        .batch_delete_row(tuanxian_start-2, tuanxian_start+3, limit=not tuanxian_lenth)\
        .merge_cell((tuanxian_start, 1), (tuanxian_end, 1), limit=tuanxian_lenth > 1)

    # 无保费
    no_baoxian_fee_length = len(no_baoixan_fee)
    no_baoxian_fee_start = tuanxian_start - 1 + tuanxian_lenth + 3 + 3 if tuanxian_lenth else tuanxian_start
    no_baoxian_fee_end = no_baoxian_fee_start + no_baoxian_fee_length - 1
    esv\
        .copy_row_down(no_baoxian_fee_start, no_baoxian_fee_length-1, set_df=no_baoixan_fee[final_list], limit=no_baoxian_fee_length)\
        .batch_delete_row(no_baoxian_fee_start-2, no_baoxian_fee_start+3, limit=not no_baoxian_fee_length)\
        .merge_cell((no_baoxian_fee_start, 1), (no_baoxian_fee_end, 1), limit=no_baoxian_fee_length > 1)
