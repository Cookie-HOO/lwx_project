import math

import pandas as pd
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen, QColor

from lwx_project.client.base import BaseWindow
from lwx_project.client.const import UI_PATH, COLOR_WHITE, COLOR_RED, COLOR_GREEN
from lwx_project.client.utils.graph_widget import GraphWidgetWrapper
from lwx_project.client.utils.table_widget import TableWidgetWrapper
from lwx_project.scene import contribution
from lwx_project.utils.excel_checker import ExcelCheckerWrapper
from lwx_project.utils.logger import logger_sys_error

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


def cell_style_func(df, i, j) -> QColor:
    contribution_value = df["贡献率"][i]
    contribution_value = float(str(contribution_value).strip("%") or 0)
    if math.isclose(contribution_value, 0) or len(df) == i+1:
        return COLOR_WHITE
    elif contribution_value > 0:
        return COLOR_RED
    elif contribution_value < 0:
        return COLOR_GREEN


class MyContributionClient(BaseWindow):
    def __init__(self):
        super(MyContributionClient, self).__init__()
        uic.loadUi(UI_PATH.format(file="contribution.ui"), self)  # 加载.ui文件
        self.setWindowTitle("期缴保费贡献率计算器——By LWX")
        self.df = None
        self.df_download = None

        self.upload_table_button.clicked.connect(self.upload_file)  # 将按钮的点击事件连接到upload_file方法
        self.download_table_button.clicked.connect(self.download_file)  # 将按钮的点击事件连接到upload_file方法
        self.alpha_slider.valueChanged.connect(self.alpha_changed)

        self.table_widget_wrapper = TableWidgetWrapper(self.table_value)

    def upload_file(self):
        file_name = self.upload_file_modal(("Excel Files", "*.xlsx"), multi=False)
        if not file_name:
            return
        cols = ["公司", "期缴保费", "去年期缴保费"]
        excel_checker = ExcelCheckerWrapper(file_name, skiprows=1)\
            .column_name_process(process_func=lambda c: str(c).replace("\n", ""))\
            .has_cols(cols)
        if excel_checker.check_any_failed():
            return self.modal("warn", f"文件校验失败：{excel_checker.reason}")
        df = excel_checker.df.copy()
        if df["公司"].values[-1] == "合计":
            df = df.drop(df.index[-1])  # 取消最后一行总计
        df = df[~((df["期缴保费"] == 0) & (df["去年期缴保费"] == 0))]  # 去掉去年和今年保费都是0的行
        self.df = df[cols]  # 将处理完的结果挂到self上
        self.table_widget_wrapper.fill_data_with_color(self.df)
        # table_widget.fill_data(self.table_value, self.df)

    def download_file(self):
        # 询问是否包含均值公司
        with_mean = self.modal("check_yes", title="下载", msg="下载是否包含「均值公司」")
        if with_mean is None:
            return
        # 询问路径
        file_path = self.download_file_modal("贡献度计算结果.xlsx")
        if not file_path or self.df_download is None:
            return
        # 保存
        if with_mean:  # 包含均值公司（当前表格中显示的）
            df = self.table_widget_wrapper.get_data_as_df()
            df.to_excel(file_path, index=False)
        else:
            self.df_download.to_excel(file_path, index=False)

    @logger_sys_error
    def alpha_changed(self, value):
        alpha = value / 100
        self.alpha_value.setText(str(alpha))
        if self.df is not None:
            # 生成表格
            df, self.df_download = contribution.main_with_args(self.df, alpha)
            self.table_widget_wrapper.fill_data_with_color(df, cell_style_func=cell_style_func)
            # table_widget.fill_data(self.table_value, df, style_func)
            company_value = df["公司"].tolist()
            contribution_value = df["贡献率"].tolist()
            contribution_num = df["__贡献率"]

            # 正和负的个数
            self.positive_num_value.setText(f"正贡献率公司：{len(contribution_num[contribution_num > 0])}个")
            self.negative_num_value.setText(f"负贡献率公司：{len(contribution_num[contribution_num < 0])}个")
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
            red_pen = QPen(Qt.red, 2, Qt.SolidLine)
            green_pen = QPen(Qt.green, 2, Qt.SolidLine)
            gray_pen = QPen(Qt.gray, 1, Qt.DashLine)

            GraphWidgetWrapper(self.graph_value)\
                .add_bin_histgram(df["__贡献率"][:-1].to_list(), q_pen_positive=red_pen, q_pen_negative=green_pen)\
                .set_y_tick(q_pen=gray_pen)\
                .draw()
