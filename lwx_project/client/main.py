from PyQt5 import uic
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow

from lwx_project.client.const import UI_PATH, STATIC_FILE_PATH
from lwx_project.client.scene.daily_baoxian_client import MyDailyBaoxianClient
from lwx_project.client.scene.monthly_communication_data_client import MyMonthlyCommunicationDataClient
from lwx_project.client.scene.monthly_east_data_client import MyMonthlyEastDataClient
from lwx_project.client.scene.monthly_profit_client import MyMonthlyProfitClient


# from lwx_project.client.scene.activity_rate import MyActivityRateClient
# from lwx_project.client.scene.contribution_client import MyContributionClient
# from lwx_project.client.scene.daily_report_client import MyDailyReportClient
# from lwx_project.client.scene.product_evaluation import MyProductEvaluationClient
# from lwx_project.client.scene.product_name_match import MyProductNameMatchClient


class MyClient(QMainWindow):
    def __init__(self):
        super(MyClient, self).__init__()
        uic.loadUi(UI_PATH.format(file="main.ui"), self)  # 加载.ui文件
        self.setWindowTitle("李文萱的工作空间")
        self.setWindowIcon(QIcon(STATIC_FILE_PATH.format(file="app.ico")))
        self.main_tab.addTab(MyDailyBaoxianClient(), '每日保险整理')
        self.main_tab.addTab(MyMonthlyCommunicationDataClient(), '每月同业交流数据汇总计算')
        self.main_tab.addTab(MyMonthlyEastDataClient(), '每月east数据汇总计算')
        self.main_tab.addTab(MyMonthlyProfitClient(), '每月利润完成情况汇总计算')
        # self.main_tab.addTab(MyActivityRateClient(), '活动率画图')
        # self.main_tab.addTab(MyContributionClient(), '贡献率计算')
        # self.main_tab.addTab(MyProductNameMatchClient(), '产品名称匹配')
