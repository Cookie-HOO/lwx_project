# 路径
import os
import sys

is_prod = os.environ.get("env") == 'prod'

# path
PROJECT_PATH = os.getcwd() if is_prod else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALL_DATA_PATH = os.path.join(PROJECT_PATH, "data")
STATIC_PATH = os.path.join(PROJECT_PATH, "static")
LOGGER_FILE_PATH = os.path.join(PROJECT_PATH, "logger.log")
ROOT_IN_EXE_PATH = sys._MEIPASS if is_prod else PROJECT_PATH

# formatter
DATE_FORMATTER = '%Y-%m-%d'
TIME_FORMATTER = '%Y-%m-%d %H.%M.%S'
FULL_TIME_FORMATTER = '%Y-%m-%d %H.%M.%S.%f'
