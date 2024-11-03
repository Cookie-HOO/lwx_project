import re

import pandas as pd

from lwx_project.scene.product_evaluation.const import *
from lwx_project.utils.conf import get_txt_conf, CSVConf
from lwx_project.utils.strings import replace_parentheses_and_comma
from lwx_project.utils.time_obj import TimeObj


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


def match_term_num(raw_xianzhong_name, baoxian_type, abbr_2, abbr_4, yinbao_and_sihang):
    """
    abbr_2: 两个字的简称
    abbr_4: 四个字的简称
    匹配期数
    0. 如果保险类型不是 有保费
        返回 空字符串
    0. 如果能够直接匹配到期数
        返回

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

    5. 如果还是没有
        TODO：需要交给用户判断（在client中）

    """
    # 0. 只有有报费的参与
    if baoxian_type != "有保费":
        return ""
    xianzhong_name = replace_parentheses_and_comma(raw_xianzhong_name)

    # 0. 特定产品的期数匹配
    df_equal = CSVConf(TERM_MATCH_PAIR_PATH, init_columns=["产品", "期数"]).get()  # 产品 | 期数
    term_num = df_equal[df_equal["产品"] == xianzhong_name]["期数"]
    if len(term_num.values) > 0:
        return term_num.values[0]

    # 1. 严格匹配
    df_strip = yinbao_and_sihang[["产品名称", "期数"]]
    df_strip["产品名称"] = yinbao_and_sihang["产品名称"].apply(replace_parentheses_and_comma)
    term_num = df_strip[df_strip["产品名称"] == xianzhong_name]["期数"]
    if len(term_num.values) > 0:
        return term_num.values[0]

    # 2. in匹配：完全在其中
    result = df_strip[df_strip['产品名称'].str.contains(xianzhong_name)]
    if len(result) > 0:
        return result.iloc[0]["期数"]

    # 3. in匹配：简称问题，两个字的简称换成4个字的简称
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
    xianzhong_name_strip = xianzhong_name
    for pattern in get_txt_conf(TERM_MATCH_UNIMPORTANT_PATTERN_PATH, list):
        xianzhong_name_strip = delete_term_notin_parentheses(xianzhong_name_strip, pattern=pattern)

    result = df_strip[df_strip['产品名称'].str.contains(xianzhong_name_strip)]
    if len(result) == 1:
        return result.iloc[0]["期数"]
    elif len(result) > 1:
        # 如果多于一个需要交给用户判断（在client中）
        return EMPTY_TERM_PLACE_HOLDER  # bad path 由用户判断

    # # 4. 用户自己维护的等价字典：险种名称可以换
    # df_equal = get_csv_conf(TERM_MATCH_EQUAL_PAIR_PATH)  # 词语 | 等价
    # dict1 = df_equal.set_index('词语')['等价'].to_dict()
    # dict2 = df_equal.set_index('等价')['词语'].to_dict()
    # equal_dict = {**dict1, **dict2}
    # xianzhong_name_replace = xianzhong_name
    # for w1, w2 in equal_dict.items():
    #     xianzhong_name_replace = xianzhong_name_replace.replace(w1, w2)
    #     result = df_strip[df_strip['产品名称'].str.contains(xianzhong_name_replace)]
    #     if len(result) == 1:
    #         return result.iloc[0]["期数"]
    #     elif len(result) > 1:
    #         # 如果多于一个需要交给用户判断（在client中）
    #         return EMPTY_TERM_PLACE_HOLDER  # bad path 由用户判断

    # 其他情况目前找不到，由用户判断
    return EMPTY_TERM_PLACE_HOLDER


def main(df_detail, df_tuanxian, df_yinbao, df_sihang, df_gerenyanglaojin, df_last_term=None):
    """
    :param df_detail: 拼接简称表之后的带简称的df
    :param df_tuanxian: 团险
    :param df_yinbao: 银保
    :param df_sihang: 私行
    :param df_gerenyanglaojin: 个人养老金
    :param df_last_term: 上期保费，如果当前是一季度，上期保费可以不传
    :return:
    """
    # 1. 数据预处理
    df_for_value = df_detail.drop(
        columns=["保险公司"]
    )
    df_for_value = df_for_value.rename(columns={
        "实际简称": "保险公司",
        "本期实现保费": "保费",
    })

    # 2. 对险种名称groupby
    # 保险公司	险种名称	{期数}	保费	{其中：一、二季度保费}	险种代码	保险责任分类	保险责任子分类	保险期限	缴费期间	总笔数	犹撤保费	退保保费	本期实现手续费收入
    df_for_value_group = df_for_value.groupby("险种名称", as_index=False).agg({
        "保险公司": "first",
        "保费": "sum",
        "险种代码": "first",
        "保险责任分类": "first",
        "保险责任子分类": "first",
        "保险期限": "first",
        "缴费期间": "first",
        "总笔数": "sum",
        "犹撤保费": "sum",
        "退保保费": "sum",
        "本期实现手续费收入": "sum",
        "产品目录统计": "first"  # 用于匹配公司简称使用，不体现在最终结果中
    })

    # 3.存储有保费、无保费、团险三种类型
    # all_tuanxian_product_df = pd.read_excel(PRODUCT_LIST_PATH, sheet_name="团险", skiprows=1)
    all_tuanxian_product = df_tuanxian["产品名称"].dropna().values
    df_for_value_group["保险类型"] = df_for_value_group.apply(lambda x: get_baoxian_type(x, all_tuanxian_product), axis=1)

    # 4. 寻找期数（只有有保费的需要找期数）
    df_for_value_group["期数"] = ""
    # yinbao_df = pd.read_excel(PRODUCT_LIST_PATH, sheet_name="银保", skiprows=1)
    # sihang_df = pd.read_excel(PRODUCT_LIST_PATH, sheet_name="私行", skiprows=1)
    # gerenyanglaojin_df = pd.read_excel(PRODUCT_LIST_PATH, sheet_name="个人养老金", skiprows=1)
    # 将三个sheet作为匹配的表：todo: 改成配置
    yinbao_and_sihang = pd.concat(
        [
            df_yinbao.dropna(subset=["产品名称"])[["产品名称", "期数"]],
            df_sihang.dropna(subset=["产品名称"])[["产品名称", "期数"]],
            df_gerenyanglaojin.dropna(subset=["产品名称"])[["产品名称", "期数"]],
        ],
        axis=0
    )
    yinbao_and_sihang["期数"] = yinbao_and_sihang["期数"].apply(lambda x: x.split("\n")[0])
    # todo: 这里可以优化，先找到所有有保费的再参与计算
    # 参考：df.loc[df['age'] >= 30, 'salary'] = df.loc[df['age'] >= 30, 'salary'].apply(lambda x: x**2)
    df_for_value_group["期数"] = df_for_value_group.apply(lambda x: match_term_num(x["险种名称"], x["保险类型"], x["产品目录统计"], x["保险公司"], yinbao_and_sihang), axis=1)
    # has_fee = df_for_value_group[df_for_value_group["保险类型"] == '有保费']
    # has_fee["期数"] = has_fee.apply(lambda x: math_term_num(x["保险类型"], x["产品目录统计"], x["保险公司"], yinbao_and_sihang), axis=1)

    no = df_for_value_group[df_for_value_group["期数"] == EMPTY_TERM_PLACE_HOLDER]

    # 5. 上期保费
    """
    {其中：一、二季度保费}列
    名字：看当前日期
        处在一季度：没有这一列
        处在二季度：{其中：一季度保费}
        处在三季度：{其中：一、二季度保费}
        处在四季度：{其中：一、二、三季度保费}
    值：
        在{上期保费.xlsx} 和 {总表1} 中 {险种名称}一样的列，对 {上期保费.xlsx} 中的 {本期实现保费} 求和
    """
    today = TimeObj()
    if today.season == 2:
        return df_for_value_group
    if df_last_term is None:
        raise ValueError(f"当前位于：{today.season}季度，需要提供上季度保费表")
    # 如果当前不是第一季度，需要拼接上期保费
    # last_season_fee = pd.read_excel(LAST_TERM_PATH, skiprows=2)
    last_season_fee_group = df_last_term.groupby("险种名称", as_index=False)["本期实现保费"].sum()
    last_season_fee_group = last_season_fee_group.rename(columns={"本期实现保费": "截止上季度实现保费"})

    df_for_value_group = df_for_value_group.merge(last_season_fee_group, how="left", on="险种名称")
    return df_for_value_group.fillna(0)

