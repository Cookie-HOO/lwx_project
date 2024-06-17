from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow

from lwx_project.client.const import UI_PATH
from lwx_project.client.scene.contribution_client import MyContributionClient
from lwx_project.client.scene.daily_report_client import MyDailyReportClient


class MyClient(QMainWindow):
    def __init__(self):
        super(MyClient, self).__init__()
        uic.loadUi(UI_PATH.format(file="main.ui"), self)  # 加载.ui文件
        self.setWindowTitle("LWX's Workspace")
        self.main_tab.addTab(MyDailyReportClient(), '日报')
        self.main_tab.addTab(MyContributionClient(), '贡献率计算')
