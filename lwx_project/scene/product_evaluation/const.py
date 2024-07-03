from lwx_project.const import *


######################## product evaluation #########################
DATA_PATH = os.path.join(ALL_DATA_PATH, "product_evaluation")
# Data路径：important
DATA_IMPORTANT_PATH = os.path.join(DATA_PATH, "important")
# Data路径：tmp
DATA_TMP_PATH = os.path.join(DATA_PATH, "tmp")
DATA_RESULT_PATH = os.path.join(DATA_PATH, "result")

PRODUCT_LIST_PATH = os.path.join(DATA_TMP_PATH, "产品目录.xlsx")
PRODUCT_DETAIL_PATH = os.path.join(DATA_TMP_PATH, "分行代理保险产品分险种销售情况统计表.xlsx")
COMPANY_ABBR_PATH = os.path.join(DATA_TMP_PATH, "对应表.xlsx")
LAST_TERM_PATH = os.path.join(DATA_TMP_PATH, "上期保费.xlsx")

EXCEL_TEMPLATE_PATH = os.path.join(DATA_IMPORTANT_PATH, "模板.xlsm")
OFFICER_COMPANY_PATH = os.path.join(DATA_IMPORTANT_PATH, "公司人员映射表.csv")
TERM_MATCH_UNIMPORTANT_PATTERN_PATH = os.path.join(DATA_IMPORTANT_PATH, "期数匹配可删词.txt")
# TERM_MATCH_EQUAL_PAIR_PATH = os.path.join(DATA_IMPORTANT_PATH, "期数匹配等价词.csv")  # 词语 | 等价
TERM_MATCH_PAIR_PATH = os.path.join(DATA_IMPORTANT_PATH, "产品期数匹配.csv")  # 产品 | 期数


# product_type_count: 5款银保产品，0款私行产品，0款团险产品
# main_product: 人保寿险鑫安两全保险(分红型)(C款)：15.64亿元，人保寿险臻鑫一生终身寿险：2.9亿元
# until_last_season：前三季度、前两季度、一季度、1-12月
# dun_qi_fee: ，其中趸缴{dunjiao_fee}亿元，期缴{qijiao_fee}亿元
TEXT_SUMMARY = """{until_last_season}，{company_name}（以下简称“{company_abbr}”）先后在我行上线{product_all_count}款产品，其中{product_type_count}。
我行代理该公司保费共{fee_total}亿元{dun_qi_fee}。
主销产品情况：{main_product}，共计{main_product_fee_num}亿元，占代理该公司整体保费规模的{main_product_fee_percent}。"""


# 匹配期数时可有可无的内容（用文件代替）
# OPTIONAL_PATTERN = ["保险", "产品", "计划", "年金", "组合", "分红"]

# 增加的之前季度保费的列名
FEE_IN_SEASON_BEFORE = {
    1: "",
    2: "其中：一季度保费",
    3: "其中：一、二季度保费",
    4: "其中：一、二、三季度保费",
}

EMPTY_TERM_PLACE_HOLDER = "—"

# 人员与公司
OFFICER_COMPANY_FILE_NAME_TEMPLATE = "【{officer}】产品后评价{last_season_char_with_year_num}.xlsm"

# 公司人员映射关系（用文件代替）
# OFFICER_MAP_COMPANY = {
#     "刘轶翔": ["太平人寿", "利安人寿", "天安人寿", "恒大人寿", "财信吉祥人寿", "招商局仁和人寿", "弘康人寿", "新华人寿"],
#     "李坤": ["中华联合人寿", "东吴人寿", "华贵人寿", "中意人寿", "英大泰和人寿", "珠江人寿", "中韩人寿", "北京人寿", "海保人寿"],
#     "黄瑞": ["人保寿险", "太平洋人寿", "君康人寿", "合众人寿", "渤海人寿", "人保健康", "中英人寿", "国华人寿"],
#     "李关义": ["平安人寿", "大家人寿", "和谐健康", "国联人寿", "信泰人寿", "和泰人寿", "国富人寿", "中信保诚"],
#     "刘昕龙": ["农银人寿", "泰康人寿", "富德生命人寿", "百年人寿", "中荷人寿", "爱心人寿"],
#     "左萌": ["中国人寿", "阳光人寿", "前海人寿", "长城人寿", "幸福人寿", "长生人寿", "复星保德信"],
#     "孟醒": ["华夏人寿", "昆仑健康", "三峡人寿", "国宝人寿", "上海人寿", "横琴人寿", "国民养老", "鼎诚人寿"],
# }