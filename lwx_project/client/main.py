from PyQt5.QtWidgets import QWidget, QLabel

from lwx_project.client.base import Background


class MyClient(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(100, 100, 500, 500)
        self.setWindowTitle('Demo')

        # 添加背景组件
        self.background = Background(self)
        self.background.setGeometry(0, 0, 500, 500)

        # 添加其他组件
        self.label = QLabel('Hello World!', self)
        self.label.setGeometry(200, 200, 100, 50)
