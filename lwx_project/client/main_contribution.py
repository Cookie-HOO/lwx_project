import pandas as pd
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QTableWidgetItem

from lwx_project.scene import contribution


class MyClient(QMainWindow):
    def __init__(self):
        super(MyClient, self).__init__()
        uic.loadUi('/Users/bytedance/py/lwx_project/lwx_project/client/ui/contribution.ui', self)  # 加载.ui文件
        self.df = None
        self.upload_button.clicked.connect(self.upload_file)  # 将按钮的点击事件连接到upload_file方法
        self.download_button.clicked.connect(self.download_file)  # 将按钮的点击事件连接到upload_file方法
        self.alpha_slider.valueChanged.connect(self.alpha_changed)
        self.alpha_value.setText(str(0.85))
        self.alpha_slider.setValue(85)
        self.setWindowTitle("期缴保费贡献率计算器——By LWX")

    def upload_file(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","Excel Files (*.xlsx)", options=options)
        if fileName:
            df = pd.read_excel(fileName, skiprows=1)
            self.df = df.drop(df.index[-1])
        self.alpha_changed(85)

    def download_file(self):
        # 弹出一个文件保存对话框，获取用户选择的文件路径
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()", "贡献度计算结果.xlsx","All Files (*);;Text Files (*.txt)", options=options)
        if filePath:
            # 下载文件
            self.df.to_excel(filePath, index=False)

    def alpha_changed(self, value):
        alpha = value / 100
        self.alpha_value.setText(str(alpha))
        print(value)
        if self.df is not None:
            self.df = contribution.main_with_args(self.df, alpha)
            # 将dataframe的数据写入QTableWidget
            self.table_value.setRowCount(self.df.shape[0])
            self.table_value.setColumnCount(self.df.shape[1])
            self.table_value.setHorizontalHeaderLabels(self.df.columns)
            for i in range(self.df.shape[0]):
                for j in range(self.df.shape[1]):
                    self.table_value.setItem(i, j, QTableWidgetItem(str(self.df.iloc[i, j])))
