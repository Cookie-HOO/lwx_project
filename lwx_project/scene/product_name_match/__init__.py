import re

import pandas as pd

from lwx_project.scene.product_name_match.const import *
from lwx_project.utils.conf import get_txt_conf
from lwx_project.utils.excel_checker import ExcelCheckerWrapper
from lwx_project.utils.strings import replace_parentheses_and_comma


def delete_notin_parentheses(text, pattern):
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
        return delete_notin_parentheses(text, pattern)
    return text


def match_product_name(raw_xianzhong_name, abbr_2, abbr_4, df_match):
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
            TODO：如果多于一个需要交给用户判断

    5. 如果还是没有
        TODO：需要交给用户判断

    """
    # 0. 只有有报费的参与
    xianzhong_name = replace_parentheses_and_comma(raw_xianzhong_name)

    # 1. 严格匹配
    df_strip = df_match[["险种名称"]]
    df_strip["险种名称"] = df_match["险种名称"].apply(replace_parentheses_and_comma)
    name_match = df_strip[df_strip["险种名称"] == xianzhong_name]["险种名称"]
    if len(name_match.values) > 0:
        return name_match.values[0]

    # 2. in匹配：完全在其中
    result = df_strip[df_strip['险种名称'].str.contains(xianzhong_name)]
    if len(result) > 0:
        return result.iloc[0]["险种名称"]

    # 3. in匹配：简称问题，两个字的简称换成4个字的简称
    if isinstance(abbr_2, str) and isinstance(abbr_4, str):
        if xianzhong_name.startswith(abbr_2):
            xianzhong_name = abbr_4 + xianzhong_name[len(abbr_2):]
            result = df_match[df_match['险种名称'].str.contains(xianzhong_name)]
            if len(result) > 0:
                return result.iloc[0]["险种名称"]
        if xianzhong_name.startswith(abbr_4):
            xianzhong_name = abbr_2 + xianzhong_name[len(abbr_4):]
            result = df_match[df_match['险种名称'].str.contains(xianzhong_name)]
            if len(result) > 0:
                return result.iloc[0]["险种名称"]

    # 4. in匹配：可有可无的内容: {保险产品}、{计划}、{年金}、{年金保险}、{分红}
    # 统一小括号，删除逗号
    xianzhong_name_strip = xianzhong_name
    for pattern in get_txt_conf(PRODUCT_MATCH_UNIMPORTANT_PATTERN_PATH, list):
        xianzhong_name_strip = delete_notin_parentheses(xianzhong_name_strip, pattern=pattern)

    result = df_strip[df_strip['险种名称'].str.contains(xianzhong_name_strip)]
    if len(result) == 1:
        return result.iloc[0]["险种名称"]
    elif len(result) > 1:
        # 如果多于一个需要交给用户判断（在client中）
        return ""  # bad path 由用户判断

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
    return ""


def main(df_product, df_match_list):
    """
    :param df_product:
    :param df_match_list:
    :return:
    """
    abbr_checker = ExcelCheckerWrapper(excel_path=COMPANY_ABBR_PATH).has_cols(["全称", "产品目录统计", "实际简称"])
    if abbr_checker.check_any_failed():
        raise ValueError

    for index, df_match in enumerate(df_match_list):
        # 1. df_match 先join 对应表（abb2，和abb4）
        df_result = pd.merge(df_product, abbr_checker.df[["全称"]])  # todo： 这里似乎不能用产品直接匹配公司
        # 2. 再取找df_match_list里面每一个的
        #   raw_xianzhong_name, abbr_2, abbr_4, df_match
        df_product[f"系统名称{index+1}"] = df_product.apply(
            lambda x: match_product_name(x["产品名称"], x["产品目录统计"], x["实际简称"], df_match),
            axis=1)
        df_product[f"年份{index+1}"] = f"{2015+index}"  # TODO: 写一个函数取获取具体年数
        pass
    pass


if __name__ == '__main__':
    df_product_path = r"D:\projects\lwx_project\data\product_name_match\upload\需匹配的产品.xlsx"
    df_list_path = [
        r"D:\projects\lwx_project\data\product_name_match\upload\2015.xlsx",
        r"D:\projects\lwx_project\data\product_name_match\upload\2016.xlsx",
        r"D:\projects\lwx_project\data\product_name_match\upload\2017.xlsx",
        r"D:\projects\lwx_project\data\product_name_match\upload\2018.xlsx",
        r"D:\projects\lwx_project\data\product_name_match\upload\2019.xlsx",
    ]
    product_excel_checker = ExcelCheckerWrapper(excel_path=df_product_path).has_cols(["产品名称"])
    if product_excel_checker.check_any_failed():
        raise ValueError
    df_product_ = product_excel_checker.df[["产品名称"]]

    df_match_list_ = []
    for path in df_list_path:
        match_excel_checker = ExcelCheckerWrapper(excel_path=path, skiprows=2).has_cols(["险种名称"])
        if match_excel_checker.check_any_failed():
            raise ValueError
        df_match_list_.append(match_excel_checker.df[["险种名称"]])

    main(df_product_, df_match_list_)
