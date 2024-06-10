# 路径
import os

is_prod = os.environ.get("env") == 'prod'

PROJECT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALL_DATA_PATH = 'data' if is_prod else os.path.join(PROJECT_PATH, "data")
STATIC_PATH = 'static' if is_prod else os.path.join(PROJECT_PATH, "static")
