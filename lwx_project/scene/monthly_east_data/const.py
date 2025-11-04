import os

from lwx_project.const import ALL_DATA_PATH, STATIC_PATH

DATA_PATH = os.path.join(ALL_DATA_PATH, "monthly_east_data")
IMPORTANT_PATH = os.path.join(DATA_PATH, "important")
DETAIL_PATH = os.path.join(DATA_PATH, "6月关联交易数据.xlsx")
CONFIG_PATH = os.path.join(IMPORTANT_PATH, "config.json")
TEMPLATE_PATH = os.path.join(IMPORTANT_PATH, "模板.xlsx")
TEMPLATE_FILE_NAME_PREFIX = "保险业务和其他类关联交易协议模板（"
TEMPLATE_FILE_NAME_SUFFIX = "农行员福+其他关联方）.xlsx"
TEMPLATE_SHEET_NAME = "关联交易协议实体"

NAME_FILE_PATH = os.path.join(IMPORTANT_PATH, "其他关联方名称.xlsx")
NAME_CODE_FILE_PATH = os.path.join(IMPORTANT_PATH, "其他关联方名称代码映射.xlsx")

SCENE_IMPORTANT_PIC_PATH = os.path.join(STATIC_PATH, "scene_important_pic", "monthly_east_data")

IMPORTANT_FILES = [
    ("模板.xlsx", os.path.join(SCENE_IMPORTANT_PIC_PATH, "模板.png")),
    ("其他关联方名称.xlsx", os.path.join(SCENE_IMPORTANT_PIC_PATH, "其他关联方名称.png")),
    ("其他关联方名称代码映射.xlsx", os.path.join(SCENE_IMPORTANT_PIC_PATH, "其他关联方名称代码映射.png")),
]
