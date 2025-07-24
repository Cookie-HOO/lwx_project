import re


def replace_parentheses_and_comma(string):
    return \
        string\
        .replace("(", "")\
        .replace(")", "")\
        .replace("（", "")\
        .replace("）", "")\
        .replace(",", "")\
        .replace("，", "")\
        .replace("「", "")\
        .replace("」", "")\
        .replace("\n", "")\
        .replace(" ", "")\
        .replace("\t", "")

def is_all_chinese(text):
    """检查字符串是否全部由汉字组成"""
    if not text:
        return False
    # 匹配从开头到结尾都是汉字的字符串
    pattern = re.compile(r'^[\u4e00-\u9fa5]+$')
    return pattern.match(text) is not None