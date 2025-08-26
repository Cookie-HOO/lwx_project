import asyncio
import os
import sys
import time
import typing

import pandas as pd
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QPushButton

from lwx_project.client.base import BaseWorker, WindowWithMainWorker
from lwx_project.client.const import UI_PATH
from lwx_project.client.utils.date_widget import DateEditWidgetWrapper
from lwx_project.client.utils.list_widget import ListWidgetWrapper
from lwx_project.client.utils.table_widget import TableWidgetWrapper
from lwx_project.const import PROJECT_PATH
from lwx_project.scene.daily_baoxian.vo import worker_manager, WorkerManager, BaoxianItem
from lwx_project.scene.daily_baoxian.workers.bid_info_worker import BidInfoWorker
from lwx_project.scene.daily_baoxian.workers.gov_buy_worker import GovBuyBaoxianItem, GovBuyWorker, gov_buy_worker
from lwx_project.utils.browser import close_all_browser_instances, get_default_browser_bin_path

from lwx_project.utils.time_obj import TimeObj

# from lwx_project.scene import product_name_match
# from lwx_project.scene.product_name_match.const import *

# from lwx_project.utils.conf import set_txt_conf, get_txt_conf
# from lwx_project.utils.excel_checker import ExcelCheckerWrapper
# from lwx_project.utils.excel_style import ExcelStyleValue
# from lwx_project.utils.file import get_file_name_without_extension

UPLOAD_REQUIRED_FILES = ["需匹配的产品"]  # 上传的文件必须要有


class Worker(BaseWorker):
    # custom_set_searched_gov_buy_baoxian_signal = pyqtSignal(GovBuyWorker)  # 自定义信号
    # custom_set_collected_gov_buy_baoxian_signal = pyqtSignal(GovBuyWorker)  # 自定义信号
    # custom_after_one_gov_buy_baoxian_done_signal = pyqtSignal(dict)  # 自定义信号

    # custom_set_searched_bid_info_baoxian_signal = pyqtSignal(BidInfoWorker)  # 自定义信号
    # custom_set_collected_bid_info_baoxian_signal = pyqtSignal(BidInfoWorker)  # 自定义信号
    # custom_after_one_bid_info_baoxian_done_signal = pyqtSignal(dict)  # 自定义信号

    custom_after_one_baoxian_done_signal = pyqtSignal(dict)
    custom_set_searched_baoxian_signal = pyqtSignal(WorkerManager)

    custom_after_one_retry_baoxian_start_signal = pyqtSignal(int)
    custom_after_one_retry_baoxian_done_signal = pyqtSignal(dict)
    custom_collect_baoxian_item_signal = pyqtSignal(BaoxianItem)

    def __init__(self):
        super().__init__()
        self.once_clean = False
        self.sec_clean = False

    def my_run(self):
        self.refresh_signal.emit("搜索中...")
        stage = self.get_param("stage")
        if stage == "search_baoxian":
            print("search_baoxian")
            start_date = self.get_param("start_date")
            end_date = self.get_param("end_date")
            browser_type = self.get_param("browser_type")
            browser_bin_path = self.get_param("browser_bin_path")

            # 修改异步策略
            if sys.platform == "win32":
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            elif sys.platform == 'darwin':
                # 设置事件循环策略：避免 SIGCHLD 问题
                policy = asyncio.WindowsSelectorEventLoopPolicy() if os.name == 'nt' else asyncio.DefaultEventLoopPolicy()
                asyncio.set_event_loop_policy(policy)

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)


            # 确保检查登录的浏览器实例已完全关闭
            close_all_browser_instances(browser_type)
            time.sleep(2)  # 等待进程关闭

            # 从网站搜索
            from lwx_project.scene.daily_baoxian.workers.gov_buy_worker import gov_buy_worker
            from lwx_project.scene.daily_baoxian.workers.bid_info_worker import bid_info_worker

            worker_manager.add_worker(bid_info_worker)
            worker_manager.add_worker(gov_buy_worker)

            # worker_manager 统一管理所有浏览器实例

            def after_one(baoxian_item):
                self.custom_collect_baoxian_item_signal.emit(baoxian_item)
                self.custom_after_one_baoxian_done_signal.emit(
                    {"baoxian_item": baoxian_item}
                )
            self.refresh_signal.emit("1. 初始化浏览器...")
            worker_manager.init_browser(browser_bin_path)
            self.refresh_signal.emit("2. 检查当前状态...")
            worker_manager.check_env()
            self.refresh_signal.emit("3. 搜索目标...")
            worker_manager.search_baoxian_by_date(
                start_date=start_date, end_date=end_date,
                call_back_after_one_done=after_one
            )
            self.refresh_signal.emit("4. 清理浏览器...")
            worker_manager.close_browser()
            close_all_browser_instances(browser_type)
            self.refresh_signal.emit("搜索完成...")
            self.custom_set_searched_baoxian_signal.emit(worker_manager)

        elif stage == "retry_baoxian":
            baoxian_items = self.get_param("baoxian_items")
            browser_bin_path = self.get_param("browser_bin_path")
            browser_type = self.get_param("browser_type")

            self.refresh_signal.emit("1. 初始化浏览器...")
            worker_manager.init_browser(browser_bin_path)
            self.refresh_signal.emit("2. 重试获取...")
            worker_manager.retry_baoxian_items(
                    baoxian_items=baoxian_items,
                    call_back_after_one_start = lambda index: self.custom_after_one_retry_baoxian_start_signal.emit(index),
                    call_back_after_one_done=lambda index, baoxian_item: self.custom_after_one_retry_baoxian_done_signal.emit({
                        "baoxian_item": baoxian_item,
                        "index": index,
                    })
                )
            self.refresh_signal.emit("3. 清理浏览器...")
            worker_manager.close_browser()
            close_all_browser_instances(browser_type)
            self.refresh_signal.emit("重试完成...")



class MyDailyBaoxianClient(WindowWithMainWorker):
    """
=========== 场景描述 ===========
找到特定文件中的 产品名称，在系统中的名称

=========== Important文件 ===========
❗📗对应表.xlsx
    要求：
        1. 列含有[实际简称]、[产品目录统计]
        2. [实际简称] 列 不能有重复
❗🔧产品匹配可删词.txt
    要求：
        1. 一行一个词语（换行符分割）
    使用方式：按顺序遍历这里的词语，挨个删除看最后是否匹配到公司

=========== 上传文件 ===========
❗需匹配的产品.xlsx
    要求：
        1. 列含有[产品名称]、[公司名称]
❗其他所有xlsx
    要求：
        1. 前两行是描述，第三行是列名
        2. 列含有[险种名称]
        3. 第二行的第一列的格式如下
            日期：xxxx年.....
注意，这里校验的过程可能耗时较长

=========== 执行逻辑 ===========
1. 公司名称 <==> important中的对应表的实际简称
    目的：得到2个字的简称
2. 匹配名称
    - 严格匹配（去掉括号）
    - in匹配
    - 简称匹配
    - 去掉不重要词后匹配

=========== 下载文件 ===========
1. 产品名称匹配.csv，列说明如下
    [产品名称]：要匹配的内容
    [公司名称]：
    [产品目录统计]：2字简称
    [实际简称]：4字简称
    [系统名称]：匹配到的内容（去重）
    [年份]：找到的年份
    [个数]：匹配到的内容（去重） 的个数
    """

    def __init__(self):
        """
        重要变量
            config_button: 高级配置按钮
                点击后展示高级配置
            product_name_match_unimportant_list_value: 配置：产品匹配中可以删除的内容，是一个text
                save_product_name_match_unimportant_list_button

            upload_file_button: 上传文件的按钮，上传文件后，将文件名和对应的时间展示在 file_date_value 这里
            do_button: 点击后进行执行

            file_list: 展示上传的文件
            product_name_match_table_value: 展示产品匹配的结果

            download_file_button: 下载最终文件的按钮
                结果excel
            reset_button: 重置当前内容的button
        """
        super(MyDailyBaoxianClient, self).__init__()
        uic.loadUi(UI_PATH.format(file="daily_baoxian.ui"), self)  # 加载.ui文件
        self.setWindowTitle("每日保险整理——By LWX")
        self.tip_loading = self.modal(level="loading", titile="加载中...", msg=None)
        self.browser_path_reset()  # 设置默认路径

        # 搜索保险的起止日期
        self.baoxian_start_date_wrapper = DateEditWidgetWrapper(self.baoxian_start_date, init_date=TimeObj() - 1)
        self.baoxian_end_date_wrapper = DateEditWidgetWrapper(self.baoxian_end_date, init_date=TimeObj() - 1)

        # 搜索保险的按钮和容器
        self.search_button.clicked.connect(self.search_baoxian)
        self.collected_baoxian_table_wrapper = TableWidgetWrapper(self.collected_baoxian_table)

        # 记录worker
        self.worker_manager: typing.Optional[WorkerManager] = None

        # 重置按钮
        self.browser_path_reset_button.clicked.connect(self.browser_path_reset)
        self.reset_button.clicked.connect(self.reset)

        # 重试按钮
        # self.retry_failed_baoxian_button.clicked.connect(self.retry_failed_baoxian)

        # 下载按钮
        self.df_result = None
        self.download_file_button.clicked.connect(
            lambda: self.download_zip_or_file_from_path(path_or_df=self.df_result, default_topic="每日保险结果"))

        self.collected_baoxian_items = []

    def register_worker(self):
        return Worker()

    def browser_path_reset(self):
        browser_type = self.browser_selector.currentText()
        self.browser_bin_path_text.setText(get_default_browser_bin_path(browser_type))

    # 核心的入口函数
    def search_baoxian(self):
        # 第一个网站搜索保险
        params = {
            "stage": "search_baoxian",
            "start_date": self.baoxian_start_date_wrapper.get().date_str,
            "end_date": self.baoxian_end_date_wrapper.get().date_str,
            "browser_bin_path": self.browser_bin_path_text.text(),
            "browser_type": self.browser_selector.currentText(),   # Chrome ｜ Edge
        }
        self.worker.add_params(params).start()

        # 增加loading tip
        self.tip_loading.set_titles(["查询招标.", "查询招标..", "查询招标..."]).show()

    def retry_failed_baoxian(self):
        params = {
            "stage": "retry_baoxian",
            "baoxian_items": self.collected_baoxian_items,
            "browser_bin_path": self.browser_bin_path_text.text(),
            "browser_type": self.browser_selector.currentText(),   # Chrome ｜ Edge
        }
        self.worker.add_params(params).start()

    def custom_set_searched_baoxian(self, worker_manager_obj: WorkerManager):
        self.tip_loading.hide()
        self.worker_manager = worker_manager_obj

    def custom_collect_baoxian_item(self, baoxian_item):
        self.collected_baoxian_items.append(baoxian_item)

    def custom_after_one_baoxian_done(self, res):
        item = res.get("baoxian_item")

        self.collected_baoxian_table_wrapper.add_row_with_color([
            item.province,
            item.bid_type,
            item.simple_title,
            item.buyer_name,
            item.budget,
            item.get_bid_until,
            item.platform + ":\n" + item.url,
            item.publish_date,
            item.title,
            item.url,
            item.detail,
            "✅" if item.success else "❌",
        ],
            # cell_widget_func=new_button
        )

    def custom_after_one_retry_baoxian_done(self, res):
        item = res.get("baoxian_item")
        index = res.get("index")
        self.collected_baoxian_table_wrapper.set_row(index, [
            item.province,
            item.bid_type,
            item.simple_title,
            item.buyer_name,
            item.budget,
            item.get_bid_until,
            item.platform + ":\n" + item.url,
            item.publish_date,
            item.title,
            item.url,
            item.detail,
            "✅" if item.success else "❌",
            ],
        )

    def custom_after_one_retry_baoxian_start(self, row_index):
        self.collected_baoxian_table_wrapper.set_cell(row_index, 11, "...")

    def reset(self):
        if self.gov_buy_q_worker.isRunning() or self.bid_info_q_worker.isRunning():
            return self.modal(level="warn", msg="运行中，无法重置，请等待执行完成")
        self.product_name_match_table_wrapper.clear()
        self.set_status_empty()
        self.status_text = ""
        self.modal("info", title="Success", msg="重置成功")

