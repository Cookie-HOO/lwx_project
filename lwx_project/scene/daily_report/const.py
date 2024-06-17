from lwx_project.const import *


######################## daily report #########################
DATA_PATH = os.path.join(ALL_DATA_PATH, "daily_report")
# Data路径：important
DATA_IMPORTANT_PATH = os.path.join(DATA_PATH, "important")
# Data路径：tmp
DATA_TMP_PATH = os.path.join(DATA_PATH, "tmp")
DAILY_REPORT_SOURCE_TEMPLATE_PATH = os.path.join(DATA_IMPORTANT_PATH, "每日报表汇总.xlsm")
DAILY_REPORT_TEMPLATE_PATH = os.path.join(DATA_TMP_PATH, "每日报表汇总.xlsm")
LEADER_WORD_TEMPLATE_PATH = os.path.join(DATA_IMPORTANT_PATH, "leader_word_template.txt")
MOTTO_TEXT_PATH = os.path.join(DATA_IMPORTANT_PATH, "motto.txt")

# Data路径：result
DATA_RESULT_PATH = os.path.join(DATA_PATH, "result")

# 宏名称
EXCEL_MARCOS = ["每日报表汇总.xlsm!粘贴", "每日报表汇总.xlsm!补充"]
