######################## contribution #########################
import os

from lwx_project.const import ALL_DATA_PATH

DATA_PATH = os.path.join(ALL_DATA_PATH, "contribution")
# Data路径：important
DATA_IMPORTANT_PATH = os.path.join(DATA_PATH, "important")
# Data路径：tmp
DATA_TMP_PATH = os.path.join(DATA_PATH, "tmp")
CONTRIBUTION_PATH = os.path.join(DATA_TMP_PATH, "贡献度.xlsx")

# Data路径: result
DATA_RESULT_PATH = os.path.join(DATA_PATH, "result")