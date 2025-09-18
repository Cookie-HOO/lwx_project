import os

from lwx_project.const import ALL_DATA_PATH

DATA_PATH = os.path.join(ALL_DATA_PATH, "monthly_east_data")
IMPORTANT_PATH = os.path.join(DATA_PATH, "important")
DETAIL_PATH = os.path.join(DATA_PATH, "6月关联交易数据.xlsx")
CONFIG_PATH = os.path.join(IMPORTANT_PATH, "config.json")
TEMPLATE_PATH = os.path.join(IMPORTANT_PATH, "模板.xlsx")
TEMPLATE_FILE_NAME_PREFIX = "保险业务和其他类关联交易协议模板（"
TEMPLATE_FILE_NAME_SUFFIX = "农行员福+其他关联方）.xlsx"

NAME_FILE = "其他关联方名称.xlsx"
NAME_CODE_FILE = "其他关联方名称代码映射.xlsx"

