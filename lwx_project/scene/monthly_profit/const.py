import os

from lwx_project.const import ALL_DATA_PATH


DATA_PATH = os.path.join(ALL_DATA_PATH, "monthly_profit")
IMPORTANT_PATH = os.path.join(DATA_PATH, "important")

TEMPLATE_FILE_NAME_PREFIX = "利润计算表模板"
TEMPLATE_FILE_NAME_SUFFIX = ".xlsx"

TEMPLATE_PATH = os.path.join(IMPORTANT_PATH, "模板.xlsx")