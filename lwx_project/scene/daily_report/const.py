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

# 结果集
RESULT_SET = {
    "代理期缴保费.xlsm", "公司网点经营情况统计表.xlsx", "农行渠道实时业绩报表.xlsx", "业绩报表.xlsx",
    "当年农", "当季农", "当月农", "当日农", "当年全", "当日全", "26当日全", "26当年全", "当日公司", "当年公司", "23当日活动率", "23当月活动率"
}
# 宏名称
EXCEL_MARCOS = ["每日报表汇总.xlsm!粘贴", "每日报表汇总.xlsm!补充"]
