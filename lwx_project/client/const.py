from PyQt5.QtGui import QColor

from lwx_project.const import *

WINDOW_INIT_SIZE = (1068, 681)
WINDOW_INIT_DISTANCE = (800, 200)
WINDOW_TITLE = "李文萱工作空间"
STATIC_FILE_PATH = os.path.join(STATIC_PATH, "{file}")
UI_PATH = os.path.join(ROOT_IN_EXE_PATH, 'ui', "{file}") if is_prod else os.path.join(os.path.dirname(__file__), "ui", "{file}")

# color
COLOR_WHITE = QColor(255, 255, 255)
COLOR_RED = QColor(245, 184, 184)
COLOR_GREEN = QColor(199, 242, 174)
