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


def is_any_chinese(text):
    """检查字符串是否包含汉字"""
    if not text:
        return False
    # 匹配包含汉字的字符串
    pattern = re.compile(r'[\u4e00-\u9fa5]')
    return pattern.search(text) is not None

def is_any_digits(text):
    """检查字符串是否含有数字"""
    for char in text:
        if char.isdigit():
            return True
    return False

def dedup_lines(text):
    """文本可能存在上下相邻的一样的行，进行去重
    但是存在两行一样的情况，需要保留，规则：如果这一行存在中文，且长度大于2，那么如果和上一行一致，则去掉这一行
    """
    lines = text.split("\n")
    deduped_lines = []
    for line in lines:
        if not line:
            continue
        if is_any_chinese(line) and len(line) > 1:
            if deduped_lines and deduped_lines[-1] == line:
                continue
        deduped_lines.append(line)
    return "\n".join(deduped_lines)

def can_convert2float(string)->bool:
    try:
        float(string)
        return True
    except ValueError:
        return False

if __name__ == '__main__':
    text1 = "nihao\nnihao\n123\n123\n你好\n你好"
    print(dedup_lines(text1))
