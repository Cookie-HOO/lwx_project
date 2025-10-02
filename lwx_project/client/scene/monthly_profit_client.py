import os
import time

from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal

from lwx_project.client.base import BaseWorker, WindowWithMainWorker
from lwx_project.client.const import UI_PATH
from lwx_project.client.utils.list_widget import ListWidgetWrapper
from lwx_project.scene.monthly_profit.const import IMPORTANT_PATH

from lwx_project.scene.monthly_profit.main import check_and_run
from lwx_project.scene.monthly_profit.utils import build_result_zip_path, build_result_zip_name
from lwx_project.utils.file import copy_file, get_file_name_with_extension, open_file_or_folder
from lwx_project.utils.mail import send_mail
from lwx_project.utils.year_month_obj import YearMonth


class Worker(BaseWorker):
    custom_check_and_run_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.once_clean = False
        self.sec_clean = False

    def my_run(self):
        stage = self.get_param("stage")
        if stage == "check_and_run":
            self.refresh_signal.emit("计算中...")
            upload_file_list: list = self.get_param("upload_file_list")
            year_month_obj: YearMonth = self.get_param("year_month_obj")
            err_msg = check_and_run(year_month_obj, upload_file_list)
            self.custom_check_and_run_signal.emit({
                "err_msg": err_msg,
            })
            self.refresh_signal.emit("✅计算完成")
            if err_msg:
                return True


class MyMonthlyProfitClient(WindowWithMainWorker):
    """
    """

    help_info_text = """
=========== 场景描述 ===========
上传当月底表、当月6807底表、同比表、业绩报表，以及一个可选的上月计算结果表
1. 当月6807底表：6行2列是 ‘产品段=6807’
2. 当月底表：7行2列是 ‘合计’，且不是6807底表
3. 同比表：3行1列是 ‘分公司’
4. 业绩报表: 2行1列是 ‘机构’
5. 可选的上月计算结果表：其他情况

程序会进行以下操作
1. 基于模板文件复制一个当月的文件
2. 将当月的值复制到上月的值（两个sheet）
3. 将上传的excel的值，复制到当月的sheet（两个sheet）
4. 调整达成表 和 明细表
- 达成表的处理
    文字：标题和注
    排序：3-25行的，对计划达成率降序
    修改字体：>100%红底黄字；>序时进度黄底黑字；其他：绿底黑字
- 明细表的处理
    标题修改
    挑选：较上月小于-50的行，补充原因
5. 截一张图 + 将达成表 和 明细表生成2个excel
6. 将这三个文件进行打包
    下载和发送都是这个压缩包
每个月做一次

=========== Important文件 ===========
❗📗模板.xlsx
    保存内容模板，每次需要复制填数

=========== 系统配置文件 ===========
❗🔧auth.json
    在data根路径下
    使用方式：{"liwenxuan_0112@126.com": "token"} 的方式进行记录

❗🔧excel_tool.xlsm
    在data根路径下
    使用方式：提供了截图的宏，可以对指定文件的指定sheet截图

=========== 注意事项 ===========
1. 上传的文件中，只四个文件或五个文件（可选的上月）
2. 如果要做一月的，那么模板复制出来后，会清空上月的数据（两个sheet）
3. 无法一次做多个月的，每次就生成当前目标年-月的
    """

    release_info_text = """
v1.1.5 完成该场景
- 上传(可多次)
- 计算、融合
- 下载、发送
    """

    def __init__(self):
        """
        重要变量
            target_year_month_text：默认是上个月对应的年份
            upload_button：上传文件按钮
                支持上传一个或多个核心团险数据excel，以及0个或1个内勤外勤人员统计
            cal_button：计算按钮
            download_file_button：下载文件按钮
                需要选定一个指定的月份，再下载
            send_file_button：发送文件按钮
            reset_button: 重置当前内容的button

            file_list：将计算完成的文件列出
        """
        super(MyMonthlyProfitClient, self).__init__()
        os.makedirs(IMPORTANT_PATH, exist_ok=True)
        uic.loadUi(UI_PATH.format(file="monthly_profit.ui"), self)  # 加载.ui文件
        self.setWindowTitle("每月利润完成情况汇总计算——By LWX")
        self.tip_loading = self.modal(level="loading", titile="加载中...", msg=None)
        # 调整初始化布局
        self.upload_vs_cal_spliter.setSizes([30,70])
        # 初始化帮助信息
        self.help_info_button.clicked.connect(
            lambda: self.modal(level="info", msg=self.help_info_text, width=800, height=400))
        self.release_info_button.clicked.connect(lambda: self.modal(level="info", msg=self.release_info_text))

        self.target_year_month_text.setText(YearMonth().sub_one_month().str_with_dash)
        # 上传文件按钮
        self.upload_button.clicked.connect(self.upload_files_action)
        # 计算按钮
        self.cal_button.clicked.connect(self.check_and_run)
        # 下载文件按钮
        self.download_file_button.clicked.connect(self.download_file_action)
        # 发送邮件按钮
        self.send_file_button.clicked.connect(self.send_file_action)
        # 重置按钮
        self.reset_button.clicked.connect(self.reset_all_action)
        # 展示上传文件结果
        self.raw_upload_list_wrapper = ListWidgetWrapper(self.raw_upload_list).bind_right_click_menu({"删除": self.right_click_menu_delete})
        self.upload_list_wrapper = ListWidgetWrapper(self.upload_list).bind_double_click_func(self.double_click_to_open)

        # 初始化信息：会被重置
        self.raw_upload_list_wrapper.clear()
        self.upload_list_wrapper.clear()
        self.target_year_month_text.setDisabled(False)
        self.raw_upload_files_map = {}
        self.year_month_obj = None
        self.my_start_at = None
        self.done_at = None

    def register_worker(self):
        return Worker()

    # 只负责上传，改变UI，不负责校验
    def upload_files_action(self):
        """上传进行校验"""
        if self.my_start_at is not None:
            self.modal(level="warn", msg="开始执行后无法上传文件")
            return
        file_names = self.upload_file_modal(["Excel Files", "*.xls*"], multi=True)
        if not file_names:
            return

        for f in file_names:
            base_f = get_file_name_with_extension(f)
            if base_f in self.raw_upload_files_map:
                self.modal(level="warn", msg=f"不允许上传重名的文件: {base_f}")
                return
            self.raw_upload_files_map[base_f] = f
            self.raw_upload_list_wrapper.add_item(base_f)

    # 点击计算：check_and_run
    def check_and_run(self):
        if len(self.raw_upload_files_map) == 0:
            self.modal(level="warn", msg="请先上传文件")
            return
        if self.my_start_at is not None:
            self.modal(level="warn", msg="开始执行后无法重复执行，请先重置")
            return
        self.year_month_obj = YearMonth.new_from_str(self.target_year_month_text.text())
        if self.year_month_obj is None:
            self.modal(level="warn", msg=f"目标年-月 {self.target_year_month_text.text()} 格式不合法\n参考: 2020-01")
            return
        self.modal(level="info", msg=f"将进行 {self.year_month_obj.str_with_dash} 的计算")
        self.target_year_month_text.setDisabled(True)
        params = {
            "stage": "check_and_run",
            "upload_file_list":  list(self.raw_upload_files_map.values()),
            "year_month_obj": self.year_month_obj,
        }
        self.worker.add_params(params).start()
        self.tip_loading.set_titles(["校验和计算.", "校验和计算..", "校验和计算..."]).show()

    def custom_check_and_run(self, result):
        self.tip_loading.hide()
        err_msg = result.get("err_msg")
        if err_msg:
            self.modal(level="warn", msg=err_msg)
            return
        self.done_at = time.time()
        self.upload_list_wrapper.fill_data_with_color([
            "✅" + build_result_zip_name(self.year_month_obj)
        ])

    def download_file_action(self):
        if self.done_at is None:
            self.modal(level="warn", msg="请先计算")
            return
        file_path = build_result_zip_path(year_month=self.year_month_obj)
        file = get_file_name_with_extension(file_path)
        target_file_path = self.download_file_modal(file)
        if not target_file_path:
            return
        copy_file(file_path, target_file_path)
        self.modal(level="info", msg="✅下载成功")

    def send_file_action(self):
        if self.done_at is None:
            self.modal(level="warn", msg="请先计算")
            return
        file_path = build_result_zip_path(year_month=self.year_month_obj)
        file = get_file_name_with_extension(file_path)

        check_yes = self.modal(level="check_yes", msg=f"即将发送：{file}", default="no")
        if not check_yes:
            return
        # 发送文件
        from_email = "liwenxuan_0112@126.com"
        to_email = "liwenxuanrs@abchina.com"
        subject = file
        attachments = [file_path]
        send_mail(
            from_email=from_email,
            to_email=to_email,
            subject=subject,
            body="",
            attachments=attachments
        )
        self.modal(level="tip", count_down=2, msg="✅发送成功(2秒后关闭)")

    def double_click_to_open(self, index, file):
        if not file.startswith("✅"):
            self.modal(level="warn", msg="请等待执行完成后再打开")
            return

        file_path = build_result_zip_path(self.year_month_obj)
        open_file_or_folder(file_path)


    def right_click_menu_delete(self, index, item):
        if self.my_start_at is not None:
            self.modal(level="warn", msg="开始执行后无法删除文件")
            return
        self.raw_upload_list_wrapper.remove_item_by_index(index)
        self.raw_upload_files_map.pop(item)

    def reset_all_action(self):
        self.raw_upload_list_wrapper.clear()
        self.upload_list_wrapper.clear()
        self.target_year_month_text.setDisabled(False)
        self.raw_upload_files_map = {}
        self.year_month_obj = None
        self.my_start_at = None
        self.done_at = None
        self.modal("info", title="Success", msg="重置成功")

