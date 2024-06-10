from lwx_project.const import *


######################## daily report #########################
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


# product_type_count: 5款银保产品，0款私行产品，0款团险产品
# main_product: 人保寿险鑫安两全保险(分红型)(C款)：15.64亿元，人保寿险臻鑫一生终身寿险：2.9亿元
# until_last_season：前三季度、前两季度、一季度、1-12月
TEXT_SUMMARY = """{year_num}年前{until_last_season}，{company_name}（以下简称“{company_abbr}”）先后在我行上线{product_all_count}款产品，其中{product_type_count}。
我行代理该公司保费共{fee_total}亿元，其中趸缴{dunjiao_fee}亿元，期缴{qijiao_fee}亿元。
主销产品情况：{main_product}，共计{main_product_fee_num}亿元，占代理该公司整体保费规模的{main_product_fee_percent}。"""


# 匹配期数时可有可无的内容
OPTIONAL_PATTERN = ["保险", "产品", "计划", "年金", "组合", "分红"]
