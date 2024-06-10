from lwx_project.const import *


######################## daily report #########################
DATA_PATH = os.path.join(ALL_DATA_PATH, "daily_report")
# Data路径：important
DATA_IMPORTANT_PATH = os.path.join(DATA_PATH, "important")
# Data路径：tmp
DATA_TMP_PATH = os.path.join(DATA_PATH, "tmp")
DAILY_REPORT_TEMPLATE_PATH = os.path.join(DATA_TMP_PATH, "每日报表汇总.xlsm")
CHEER_UP_TEXT_PATH = os.path.join(DATA_TMP_PATH, "cheer_up.txt")

# Data路径：resultc
DATA_RESULT_PATH = os.path.join(DATA_PATH, "result")

# 宏名称
EXCEL_MARCOS = ["每日报表汇总.xlsm!粘贴", "每日报表汇总.xlsm!补充"]

# 文案
TEXT_CHEER_UP = """[太阳][太阳][太阳]{text_cheer_up}。{char_season}季度代理农银人寿期缴计划及{month_num}月计划已经下发，望各分行全力推进{char_season}季度业务进度，积极部署多项措施，严格把控业务品质，切实减少犹豫期撤单情况的发生，补缺口，追进度，推动业务平台持续提升，加油[拳头][拳头][拳头]"""