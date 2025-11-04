import os

from lwx_project.const import ALL_DATA_PATH, STATIC_PATH

DATA_PATH = os.path.join(ALL_DATA_PATH, "monthly_communication_data")
IMPORTANT_PATH = os.path.join(DATA_PATH, "important")
DETAIL_PATH = os.path.join(DATA_PATH, "6月关联交易数据.xlsx")
CONFIG_PATH = os.path.join(IMPORTANT_PATH, "config.json")
TEMPLATE_PATH = os.path.join(IMPORTANT_PATH, "模板.xlsx")

CALED_FILE = "{month}月同业交流数据.xlsx"
BEFORE_CAL_FILE = "{month}月核心团险数据"

SCENE_IMPORTANT_PIC_PATH = os.path.join(STATIC_PATH, "scene_important_pic", "monthly_communication_data")
IMPORTANT_FILES = [
    ("模板.xlsx", os.path.join(SCENE_IMPORTANT_PIC_PATH, "模板.png")),
]