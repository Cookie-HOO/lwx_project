import os

from lwx_project.const import ALL_DATA_PATH

DATA_PATH = os.path.join(ALL_DATA_PATH, "monthly_communication_data")
IMPORTANT_PATH = os.path.join(DATA_PATH, "important")
DETAIL_PATH = os.path.join(DATA_PATH, "6月关联交易数据.xlsx")
CONFIG_PATH = os.path.join(IMPORTANT_PATH, "config.json")
TEMPLATE_PATH = os.path.join(IMPORTANT_PATH, "模板.xlsx")

