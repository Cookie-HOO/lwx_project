from lwx_project.const import *


######################## daily report #########################
DATA_PATH = os.path.join(ALL_DATA_PATH, "daily_report")
# Data路径：important
DATA_IMPORTANT_PATH = os.path.join(DATA_PATH, "important")
# Data路径：tmp
DATA_TMP_PATH = os.path.join(DATA_PATH, "tmp")
# Data路径：result
DATA_RESULT_PATH = os.path.join(DATA_PATH, "result")

DAILY_REPORT_SOURCE_TEMPLATE_PATH = os.path.join(DATA_IMPORTANT_PATH, "每日报表汇总.xlsm")
DAILY_REPORT_TMP_TEMPLATE_PATH = os.path.join(DATA_TMP_PATH, "每日报表汇总.xlsm")
DAILY_REPORT_RESULT_TEMPLATE_PATH = os.path.join(DATA_RESULT_PATH, "每日报表汇总.xlsm")
LEADER_WORD_TEMPLATE_PATH = os.path.join(DATA_IMPORTANT_PATH, "leader_word_template.txt")
MOTTO_TEXT_PATH = os.path.join(DATA_IMPORTANT_PATH, "motto.txt")

# 结果集
KEY_RESULT_FILE_SET = {
    "代理期缴保费.xlsm", "公司网点经营情况统计表.xlsx", "农行渠道实时业绩报表.xlsx", "业绩报表.xlsx",
    "当年农.xlsx", "当季农.xlsx", "当月农.xlsx", "当日农.xlsx", "当年全.xlsx", "当日全.xlsx", "26当日全.xlsx", "26当年全.xlsx", "当日公司.xlsx", "当年公司.xlsx", "23当日活动率.xlsx", "23当月活动率.xlsx",
    "每日报表汇总.xlsm"
}
# 无参调用宏名称
EXCEL_MARCOS = ["每日报表汇总.xlsm!粘贴", "每日报表汇总.xlsm!补充", ]

EXCEL_PIC_MARCO = "每日报表汇总.xlsm!生成图片"
