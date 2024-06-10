from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtGui import QPixmap

from lwx_project.client.const import *


class Background(QWidget):
    def __init__(self, parent=None):
        super(Background, self).__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setGeometry(100, 100, 500, 500)
        self.setWindowTitle('Background Demo')

        # 设置背景图片
        self.background = QLabel(self)
        self.background.setPixmap(QPixmap(STATIC_FILE_PATH.format(file="background1.jpg")))
        self.background.setGeometry(0, 0, 500, 500)


