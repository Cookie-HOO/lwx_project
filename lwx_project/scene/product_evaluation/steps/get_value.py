import re

import pandas as pd

from lwx_project.scene.product_evaluation.const import *
from lwx_project.utils.string import replace_parentheses_and_comma


def get_baoxian_type(df, all_baoxian_product):
    baoxian_name = df["险种名称"]
    baoxian_fee = df["保费"]
    baoxian_zerenfenlei = df["保险责任分类"]
    cond_tuanti = "团体" in baoxian_name
    cond_in_list = baoxian_name in all_baoxian_product
    cond_jiaotongyiwai = baoxian_zerenfenlei == "意外伤害保险"
    if cond_tuanti or cond_in_list or cond_jiaotongyiwai:
        return "团险"
    if baoxian_fee <= 0:
        return "无保费"
    return "有保费"

def delete_term_notin_parentheses(text, pattern):
    """删除不在小括号中的特定pattern，即第一个出现此pattern之前的左右小括号的数量一致
    :param text: 全都统一为了中文括号
    :param pattern:
    :return:
    """
    match = re.search(pattern, text)
    if not match:
        return text
    if text[:match.start()].count("）") == text[:match.start()].count("（"):
        text = text[:match.start()] + text[match.end():]
        return delete_term_notin_parentheses(text, pattern)
    return text

def math_term_num(raw_xianzhong_name, abbr_2, abbr_4, yinbao_and_sihang):
    """
    abbr_2: 两个字的简称
    abbr_4: 四个字的简称
    匹配期数
    1. 严格
        删除以下内容后完全一致，完全一致
            删除中英文小括号
            删除中英文逗号

    2. in匹配（删除括号和中英文）
        完全包含在 {产品目录.xlsx} 中，取期数最小的

    3. 严格匹配: 产品目录不动
        公司全称替换为公司简称后，完全一致
            前两个字 如果是简称，换成4个字的简称
            前四个字 如果是简称，换成2个字的简称

    4. in匹配: 产品目录不动
        可有可无：{保险产品}、{计划}、{年金}、{年金保险}、{分红}
            可有可无的东西不能在小括号中，比如（分红型）不能删
            TODO：如果多于一个需要交给用户判断（在client中）

    5. 用户的自定义规则
        A -> B
    6. 如果还是没有
        TODO：需要交给用户判断（在client中）

    """
    # 1. 严格匹配
    df_strip = yinbao_and_sihang[["产品名称", "期数"]]
    df_strip["产品名称"] = yinbao_and_sihang["产品名称"].apply(replace_parentheses_and_comma)
    xianzhong_name = replace_parentheses_and_comma(raw_xianzhong_name)
    term_num = df_strip[df_strip["产品名称"] == xianzhong_name]["期数"]
    if term_num.values:
        return term_num.values[0]

    # 2. in匹配：完全在其中
    result = df_strip[df_strip['产品名称'].str.contains(xianzhong_name)]
    if len(result) > 0:
        return result.iloc[0]["期数"]

    # 3. in匹配：简称问题
    if isinstance(abbr_2, str) and isinstance(abbr_4, str):
        if xianzhong_name.startswith(abbr_2):
            xianzhong_name = abbr_4 + xianzhong_name[len(abbr_2):]
            result = yinbao_and_sihang[yinbao_and_sihang['产品名称'].str.contains(xianzhong_name)]
            if len(result) > 0:
                return result.iloc[0]["期数"]
        if xianzhong_name.startswith(abbr_4):
            xianzhong_name = abbr_2 + xianzhong_name[len(abbr_4):]
            result = yinbao_and_sihang[yinbao_and_sihang['产品名称'].str.contains(xianzhong_name)]
            if len(result) > 0:
                return result.iloc[0]["期数"]

    # 4. in匹配：可有可无的内容: {保险产品}、{计划}、{年金}、{年金保险}、{分红}
    # 统一小括号，删除逗号
    xianzhong_name_uni_parentheses = raw_xianzhong_name.replace(",", "").replace("，", "").replace("(", "（").replace(")", "）")
    xianzhong_name_strip = xianzhong_name_uni_parentheses
    for pattern in OPTIONAL_PATTERN:
        xianzhong_name_strip = delete_term_notin_parentheses(xianzhong_name_strip, pattern=pattern)

    result = df_strip[df_strip['产品名称'].str.contains(xianzhong_name_strip)]
    if len(result) == 1:
        return result.iloc[0]["期数"]
    elif len(result) > 1:
        # 如果多于一个需要交给用户判断（在client中）
        pass

    # 其他情况目前找不到，由用户判断
    # 5. 用户自己维护的等价字典
    #  - A -> B  TODO   新华保险 -> 新华人寿  很多钱
    pass
    return "找不到"


def main(df):
    # 1. 数据预处理
    df_for_value = df.drop(
        columns=["保险公司"]
    )
    df_for_value = df_for_value.rename(columns={
        "实际简称": "保险公司",
        "本期实现保费": "保费",
    })

    # 2.存储有保费、无保费、团险三种类型
    all_tuanxian_product_df = pd.read_excel(PRODUCT_LIST_PATH, sheet_name="团险", skiprows=1)
    all_tuanxian_product = all_tuanxian_product_df["产品名称"].dropna().values
    df_for_value["__保险类型"] = df_for_value.apply(lambda x: get_baoxian_type(x, all_tuanxian_product), axis=1)

    # 3. 寻找期数（只有有保费的需要找期数）
    df_for_value["期数"] = ""
    yinbao_df = pd.read_excel(PRODUCT_LIST_PATH, sheet_name="银保", skiprows=1)
    sihang_df = pd.read_excel(PRODUCT_LIST_PATH, sheet_name="私行", skiprows=1)
    yinbao_and_sihang = pd.concat(
        [
            yinbao_df.dropna(subset=["产品名称"])[["产品名称", "期数"]],
            sihang_df.dropna(subset=["产品名称"])[["产品名称", "期数"]],
        ],
        axis=0
    )
    yinbao_and_sihang["期数"] = yinbao_and_sihang["期数"].apply(lambda x: x.split("\n")[0])
    has_fee = df_for_value[df_for_value["__保险类型"] == '有保费']
    has_fee["期数"] = has_fee.apply(lambda x: math_term_num(x["险种名称"], x["产品目录统计"], x["保险公司"], yinbao_and_sihang), axis=1)

    no = has_fee[has_fee["期数"]=="找不到"]
    pass

