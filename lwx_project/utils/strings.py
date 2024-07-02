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
