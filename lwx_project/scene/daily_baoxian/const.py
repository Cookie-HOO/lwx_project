# 中国省市信息
import os.path

from lwx_project.const import ALL_DATA_PATH

PROVINCES = [
    # 23 省
    "河北省", "山西省", "辽宁省", "吉林省", "黑龙江省",
    "江苏省", "浙江省", "安徽省", "福建省", "江西省",
    "山东省", "河南省", "湖北省", "湖南省", "广东省",
    "海南省", "四川省", "贵州省", "云南省",
    "陕西省", "甘肃省", "青海省", "台湾省",

    # 5 自治区
    "内蒙古自治区",
    "广西壮族自治区",
    "西藏自治区",
    "宁夏回族自治区",
    "新疆维吾尔自治区",

    # 4 直辖市
    "北京市",
    "天津市",
    "上海市",
    "重庆市",

    # 2 特别行政区
    "香港特别行政区",
    "澳门特别行政区"
]

# 中国省市简写
PROVINCES_ABBR = [

    "河北", "山西", "辽宁", "吉林", "黑龙江",
    "江苏", "浙江", "安徽", "福建", "江西",
    "山东", "河南", "湖北", "湖南", "广东",
    "海南", "四川", "贵州", "云南",
    "陕西", "甘肃", "青海", "台湾",

    "内蒙古",
    "广西",
    "西藏",
    "宁夏",
    "新疆",

    "北京",
    "天津",
    "上海",
    "重市",

    "香港",
    "澳门"
]

# 回归文件路径

DATA_PATH = os.path.join(ALL_DATA_PATH, "daily_baoxian")
# REGRESSION_PATH = os.path.join(DATA_PATH, "近期团险招标信息一览表.csv")
REGRESSION_PATH = os.path.join(DATA_PATH, "清洗结果.csv")
# REGRESSION_PATH1 = os.path.join(DATA_PATH, "结果1.csv")

IMPORTANT_PATH = os.path.join(DATA_PATH, "important")
OLD_RESULT_PATH = os.path.join(IMPORTANT_PATH, "近期团险招标信息一览表.xlsx")