import math

import pandas as pd
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen, QColor
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QGraphicsScene, QMessageBox

from lwx_project.client.const import UI_PATH
from lwx_project.client.utils import table_widget
from lwx_project.scene import contribution

"""
贡献度计算

输入：
    一张excel表，要求第一个sheet
        1. 第二行是列名：公司、期缴保费、去年期缴保费 三列
        2. 最后一行是总计
    动态调整的alpha值

输出
    1. excel增加三列：同比、增量、贡献率
    2. 贡献率的分布图


贡献率计算规则
    1. 增量贡献率
        各公司的增量：即 （期缴保费 - 去年期缴保费）的均值的贡献程度
    2. 存量贡献率
        各公司的 期缴保费，对期缴保费均值的贡献程度
    3. 贡献率：
        alpha * 存量贡献率  + (1-alpha) * 增量贡献率
"""


def style_func(df, i, j):
    contribution_value = df["贡献率"][i]
    contribution_value = float(str(contribution_value).strip("%") or 0)
    if math.isclose(contribution_value, 0) or len(df) == i+1:
        return QColor(255, 255, 255)
    elif contribution_value > 0:
        return QColor(245, 184, 184)
    elif contribution_value < 0:
        return QColor(199, 242, 174)


class MyContributionClient(QMainWindow):
    def __init__(self):
        super(MyContributionClient, self).__init__()
        uic.loadUi(UI_PATH.format(file="contribution.ui"), self)  # 加载.ui文件
        self.setWindowTitle("期缴保费贡献率计算器——By LWX")
        self.df = None
        # self.alpha_value.setText(str(0.85))
        # self.alpha_slider.setValue(85)

        self.upload_table_button.clicked.connect(self.upload_file)  # 将按钮的点击事件连接到upload_file方法
        self.download_table_button.clicked.connect(self.download_file)  # 将按钮的点击事件连接到upload_file方法
        self.alpha_slider.valueChanged.connect(self.alpha_changed)

    def upload_file(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","Excel Files (*.xlsx)", options=options)
        if not fileName:
            return
        df = pd.read_excel(fileName, skiprows=1)
        df = df.drop(df.index[-1])  # 取消最后一行总计
        df.columns = [i.replace("\n", "") for i in df.columns]
        # df.drop(df.index[-1], inplace=True)
        cols = ["公司", "期缴保费", "去年期缴保费"]
        for col in cols:
            if col not in df.columns:
                QMessageBox.warning(self, "Warning", f"上传的文件缺少：{col}")
                return
        self.df = df[cols]
        table_widget.fill_data(self.table_value, self.df)

    def download_file(self):
        # 弹出一个文件保存对话框，获取用户选择的文件路径
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()", "贡献度计算结果.xlsx","All Files (*);;Text Files (*.txt)", options=options)
        if filePath:
            df = table_widget.get_data(self.table_value)
            # 将数据转换为DataFrame
            df.to_excel(filePath, index=False)

    def alpha_changed(self, value):
        alpha = value / 100
        self.alpha_value.setText(str(alpha))
        if self.df is not None:
            # 生成表格
            df = contribution.main_with_args(self.df, alpha)
            table_widget.fill_data(self.table_value, df, style_func)
            company_value = df["公司"].tolist()
            contribution_value = df["贡献率"].tolist()

            # 前五和倒五
            if len(company_value) > 1:
                self.rank_1.setText(f'{company_value[0]}: {contribution_value[0]}')
                self.rank_neg_1.setText(f'{company_value[-2]}: {contribution_value[-2]}')
            if len(company_value) > 2:
                self.rank_2.setText(f'{company_value[1]}: {contribution_value[1]}')
                self.rank_neg_2.setText(f'{company_value[-3]}: {contribution_value[-3]}')
            if len(company_value) > 3:
                self.rank_3.setText(f'{company_value[2]}: {contribution_value[2]}')
                self.rank_neg_3.setText(f'{company_value[-4]}: {contribution_value[-4]}')
            if len(company_value) > 4:
                self.rank_4.setText(f'{company_value[3]}: {contribution_value[3]}')
                self.rank_neg_4.setText(f'{company_value[-5]}: {contribution_value[-5]}')
            if len(company_value) > 5:
                self.rank_5.setText(f'{company_value[4]}: {contribution_value[4]}')
                self.rank_neg_5.setText(f'{company_value[-6]}: {contribution_value[-6]}')

            # 画直方图
            self.graph_value.setScene(self.create_scene(df))

    def create_scene(self, df, with_y_tick=True):
        data = df["__贡献率"]
        data = data[:-1]  # 去掉总计
        scene = QGraphicsScene(self)
        scene.setSceneRect(0, 0, self.graph_value.width(), self.graph_value.height())
        x = self.graph_value.width() - 20
        y = (self.graph_value.height()-20) / 2
        width = self.graph_value.width() / len(data)
        height = self.graph_value.height() / 2 / max(data)

        red_pen = QPen(Qt.red, 2, Qt.SolidLine)
        green_pen = QPen(Qt.green, 2, Qt.SolidLine)
        if with_y_tick:
            gray_pen = QPen(Qt.gray, 1, Qt.DashLine)
            y_value_list = [i/10 for i in range(-30, 31, 1)]
            for y_real_value in y_value_list:
                if y_real_value >= 0:
                    y_value = y - y_real_value * height
                    scene.addLine(0, y_value, x, y_value, gray_pen)
                else:
                    y_value = y + abs(y_real_value) * height
                    scene.addLine(0, y_value, x, y_value, gray_pen)
                scene.addLine(0, y, x, y, gray_pen)

        for value in data:
            if value >= 0:
                scene.addLine(x, y, x, y - value * height, red_pen)
            else:
                scene.addLine(x, y, x, y + abs(value) * height, green_pen)
            x -= width
        return scene
