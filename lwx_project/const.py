# 路径
import os
import sys

is_prod = os.environ.get("env") == 'prod'

PROJECT_PATH = '' if is_prod else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALL_DATA_PATH = os.path.join(PROJECT_PATH, "data")
STATIC_PATH = os.path.join(PROJECT_PATH, "static")
ROOT_IN_EXE_PATH = sys._MEIPASS if is_prod else PROJECT_PATH
