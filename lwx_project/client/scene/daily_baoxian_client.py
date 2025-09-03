import asyncio
import json
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
from lwx_project.scene.daily_baoxian import merge_result
from lwx_project.scene.daily_baoxian.const import OLD_RESULT_PATH, CONFIG_PATH
from lwx_project.scene.daily_baoxian.vo import worker_manager, WorkerManager, BaoxianItem
from lwx_project.scene.daily_baoxian.workers.bid_info_worker import BidInfoWorker
from lwx_project.scene.daily_baoxian.workers.gov_buy_worker import GovBuyBaoxianItem, GovBuyWorker, gov_buy_worker
from lwx_project.utils.browser import close_all_browser_instances, get_default_browser_bin_path
from lwx_project.utils.file import copy_file
from lwx_project.utils.mail import send_mail

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

    help_info_text = """
=========== 场景描述 ===========
收集指定网站的指定条件的招标信息，并融合之前收集到的信息，并支持发送邮件
1. 搜索招标信息
2. 可以手动修改关键信息
3. 点击保存会融合所有信息
4. 可选一件发送邮件

=========== Important文件 ===========
❗📗近期团险招标信息一览表.xlsx
    之前收集的招标信息，用于融合
    每次搜索后会融合之前的信息

❗auth.json
    存储鉴权信息，主要是邮箱的登陆信息
    格式：{"xx@xx.com": "授权码"}

❗🔧config.json
    使用方式：使用过程中的配置文件，自动记录，无需手动管理

=========== 执行逻辑 ===========
1. 在「中国政府采购网」搜索，支持：公开招标,竞争性谈判,竞争性磋商
2. 在「中国招标投标公共服务平台」搜索，支持「公开招标」
3. 重点收集：截止日期/金额/采购方

=========== 注意事项 ===========
1. 先检查日期，再点击搜索，默认是昨天
2. 如果出现验证码，就进行验证，验证后会自动继续收集
3. 收集完成后，需要修改则修改，一定要点击保存，发送邮件时会进行提示
4. 只能点击一次保存，如果还需要修改，去important目录进行修改
    """

    release_info_text = """
v1.1.0: 实现基础版本的搜索
- 搜索
- 修改、保存、融合
- 发送邮件
    """

    step1_help_info_text = """设置日期后，进行搜索，需要指定浏览器路径（会强制关闭所有打开的浏览器）"""

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
        # 初始化帮助信息
        self.help_info_button.clicked.connect(lambda: self.modal(level="info", msg=self.help_info_text, width=800, height=400))
        self.release_info_button.clicked.connect(lambda: self.modal(level="info", msg=self.release_info_text))
        self.step1_help_info_button.clicked.connect(lambda: self.modal(level="info", msg=self.step1_help_info_text))
        # self.demo_button.hide()  # todo 演示功能先隐藏

        # 设置默认路径
        try:
            with open(CONFIG_PATH) as f:
                self.config = json.loads(f.read())
        except Exception:
            self.config = {"browser_bin_path": get_default_browser_bin_path("Chrome"), "browser_type": "Chrome"}
            with open(CONFIG_PATH, "w") as f:
                f.write(json.dumps(self.config))
        self.init_browser()  # 初始化上次的执行路径和类型

        # 搜索保险的起止日期
        self.baoxian_start_date_wrapper = DateEditWidgetWrapper(self.baoxian_start_date, init_date=TimeObj() - 1)
        self.baoxian_end_date_wrapper = DateEditWidgetWrapper(self.baoxian_end_date, init_date=TimeObj() - 1)

        # 搜索保险的按钮和容器
        self.search_button.clicked.connect(self.search_baoxian)
        self.collected_baoxian_table_wrapper = TableWidgetWrapper(self.collected_baoxian_table)
        self.collected_baoxian_table_wrapper.set_col_width(0, 60).set_col_width(1, 60).set_col_width(3, 260).set_col_width(8, 260)

        # 记录worker
        self.worker_manager: typing.Optional[WorkerManager] = None

        # 重置按钮
        self.browser_path_reset_button.clicked.connect(self.browser_path_reset)
        self.reset_button.clicked.connect(self.reset)

        # 重试按钮
        # self.retry_failed_baoxian_button.clicked.connect(self.retry_failed_baoxian)

        # 下载按钮
        self.df_result = None
        self.save_file_button.clicked.connect(self.save_file)
        self.send_file_button.clicked.connect(self.send_file)

        self.collected_baoxian_items = []
        self.has_saved = None

    def register_worker(self):
        return Worker()

    def browser_path_reset(self):
        browser_type = self.browser_selector.currentText()
        self.browser_bin_path_text.setText(get_default_browser_bin_path(browser_type))

    def init_browser(self):
        """
        从配置文件中初始化上次执行的 browser_type 和 browser_path
        """

        """
        {
          "browser_bin_path": "",
          "browser_type": "chrome"
        }
        """
        browser_type = self.config.get("browser_type") or self.browser_selector.currentText()
        browser_bin_path = self.config.get("browser_bin_path") or get_default_browser_bin_path(browser_type)

        index = self.browser_selector.findText(browser_type)
        if index >= 0:
            self.browser_selector.setCurrentIndex(index)
        self.browser_bin_path_text.setText(browser_bin_path)

    # 核心的入口函数
    def search_baoxian(self):
        # 第一个网站搜索保险
        check_yes = self.modal(level="check_yes", msg=f"继续将关闭所有{self.browser_selector.currentText()}浏览器，请确保所有浏览器上的工作已保存")
        if not check_yes:
            return
        # 保存配置
        self.config["browser_bin_path"] = self.browser_bin_path_text.text()
        self.config["browser_type"] = self.browser_selector.currentText()
        with open(CONFIG_PATH, "w") as f:
            f.write(json.dumps(self.config))
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

        # 【提示信息】：获取状态、是否选择
        # 【关键信息】：详情链接（复制）、项目名称、采购单位名称、预算/限价（万元）、获取招标文件的截止日期、地区
        # 【参考信息】：原标题、发布日期、招采平台、采购方式、详情信息、链接
        self.collected_baoxian_table_wrapper.add_rich_widget_row([
            {
                "type": "readonly_text",  # 获取状态
                "value": "✅" if item.success else "❌",
            }, {
                "type": "checkbox",  # 是否选择
                "value": item.success and bool(item.simple_title or item.publish_date or item.get_bid_until),
            }, {
                "type": "button_group",  # 详情链接（点击即可复制）
                "values": [
                    {
                        "value": "复制链接",
                        "onclick": lambda row_index, col_index, row, url=item.url: self.copy2clipboard(url),
                    }
                ],
            }, {  # 关键信息：项目名称
                "type": "editable_text",
                "value": item.simple_title,
            }, {  # 关键信息：采购单位名称
                "type": "editable_text",
                "value": item.buyer_name,
            }, {  # 关键信息：预算
                "type": "editable_text",
                "value": item.budget,
            }, {  # 关键信息：截止日期
                "type": "editable_text",
                "value": item.get_bid_until,
            }, {  # 参考信息：地区
                "type": "editable_text",
                "value": item.province,
            }, {  # 参考信息：原标题
                "type": "readonly_text",
                "value": item.title,
            }, {  # 参考信息：发布日期
                "type": "readonly_text",
                "value": item.publish_date,
            }, {  # 参考信息：招采平台
                "type": "readonly_text",
                "value": item.platform,
            }, {  # 参考信息：采购方式
                "type": "readonly_text",
                "value": item.bid_type,
            }, {  # 参考信息：详细内容
                "type": "readonly_text",
                "value": item.detail,
            }, {  # 参考信息：链接
                "type": "readonly_text",
                "value": item.url,
            },
        ])
        #
        # self.collected_baoxian_table_wrapper.add_row_with_color([
        #     item.province,
        #     item.bid_type,
        #     item.simple_title,
        #     item.buyer_name,
        #     item.budget,
        #     item.get_bid_until,
        #     item.platform + ":\n" + item.url,
        #     item.publish_date,
        #     item.title,
        #     item.url,
        #     item.detail,
        #     "✅" if item.success else "❌",
        # ],
        #     # cell_widget_func=new_button
        # )

    def custom_after_one_retry_baoxian_done(self, res):
        """每一条baoxian item 收集完成后的回调：记录到table容器中
        获取状态、是否选择、详情链接、项目名称、采购单位名称、预算/限价（万元）、获取招标文件的截止日期、原标题、地区、发布日期、招采平台、采购方式、详情信息
        """
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

    def save_file(self):
        df = self.collected_baoxian_table_wrapper.get_data_as_df()
        # 处理信息
        merge_result.merge(df)
        self.modal(level="tip", count_down=1, title="1秒后关闭", msg="✅保存成功")
        self.has_saved=True
        self.save_file_button.setEnabled(False)
        self.save_file_button.setToolTip('无法重复保存，请去important目录进行修改')

    def send_file(self):
        if not self.has_saved:
            check_yes = self.modal(level="check_yes", msg="还未保存，是否直接发送", default="no")
            if not check_yes:
                return
        # 发送文件
        merge_result.send()
        self.modal(level="tip", count_down=1, title="1秒后关闭", msg="✅发送成功")

    def reset(self):
        if self.worker_manager and self.worker_manager.running:
            return self.modal(level="warn", msg="运行中，无法重置，请等待执行完成")
        self.collected_baoxian_table_wrapper.clear_content()
        self.set_status_empty()
        self.status_text = ""
        self.has_saved=None
        self.modal("info", title="Success", msg="重置成功")
