from lwx_project.const import *


######################## product name match #########################
DATA_PATH = os.path.join(ALL_DATA_PATH, "product_name_match")
# Data路径：important
DATA_IMPORTANT_PATH = os.path.join(DATA_PATH, "important")
# Data路径：tmp
DATA_TMP_PATH = os.path.join(DATA_PATH, "tmp")
DATA_RESULT_PATH = os.path.join(DATA_PATH, "result")


PRODUCT_MATCH_UNIMPORTANT_PATTERN_PATH = os.path.join(DATA_IMPORTANT_PATH, "产品匹配可删词.csv")
COMPANY_ABBR_PATH = os.path.join(DATA_IMPORTANT_PATH, "对应表.xlsx")
