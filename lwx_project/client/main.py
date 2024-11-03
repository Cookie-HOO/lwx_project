from PyQt5 import uic
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow

from lwx_project.client.const import UI_PATH, STATIC_FILE_PATH
from lwx_project.client.scene.activity_rate import MyActivityRateClient
from lwx_project.client.scene.contribution_client import MyContributionClient
from lwx_project.client.scene.daily_report_client import MyDailyReportClient
from lwx_project.client.scene.product_evaluation import MyProductEvaluationClient
from lwx_project.client.scene.product_name_match import MyProductNameMatchClient


class MyClient(QMainWindow):
    def __init__(self):
        super(MyClient, self).__init__()
        uic.loadUi(UI_PATH.format(file="main.ui"), self)  # 加载.ui文件
        self.setWindowTitle("李文萱的工作空间")
        self.setWindowIcon(QIcon(STATIC_FILE_PATH.format(file="app.ico")))
        self.main_tab.addTab(MyDailyReportClient(), '日报')
        self.main_tab.addTab(MyProductEvaluationClient(), '产品评价')
        self.main_tab.addTab(MyActivityRateClient(), '活动率画图')
        self.main_tab.addTab(MyContributionClient(), '贡献率计算')
        self.main_tab.addTab(MyProductNameMatchClient(), '产品名称匹配')
