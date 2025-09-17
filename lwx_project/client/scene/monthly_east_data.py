import json
import os
import time

from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal

from lwx_project.client.base import BaseWorker, WindowWithMainWorker
from lwx_project.client.const import UI_PATH
from lwx_project.client.utils.list_widget import ListWidgetWrapper
from lwx_project.client.utils.table_widget import TableWidgetWrapper
from lwx_project.scene.monthly_communication_data.check_excel import check_excels, UploadInfo
from lwx_project.scene.monthly_communication_data.const import CONFIG_PATH, IMPORTANT_PATH, BEFORE_CAL_FILE, CALED_FILE
from lwx_project.scene.monthly_communication_data.main import cal_and_merge
from lwx_project.utils.file import copy_file, get_file_name_with_extension
from lwx_project.utils.mail import send_mail
from lwx_project.utils.time_obj import TimeObj


class Worker(BaseWorker):
    custom_after_check_upload_signal = pyqtSignal(dict)
    custom_after_one_cal_signal = pyqtSignal(dict)
    custom_after_all_cal_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.once_clean = False
        self.sec_clean = False

    def my_run(self):
        stage = self.get_param("stage")
        if stage == "check_upload":
            self.refresh_signal.emit("上传文件校验中...")
            file_path_list = self.get_param("file_path_list")
            is_success, error_msg, res = check_excels(file_path_list)

            self.custom_after_check_upload_signal.emit({
                "is_success": is_success,
                "error_msg": error_msg,
                "res": res,
            })


        elif stage == "start_cal":
            upload_info: UploadInfo = self.get_param("upload_info")
            code_rules_dict = self.get_param("code_rules_dict")

            files_map = cal_and_merge(
                upload_info=upload_info,
                code_rules_dict=code_rules_dict,
                after_one_done_callback=lambda month: self.custom_after_one_cal_signal.emit({
                    "month": month
                }),
            )
            self.refresh_signal.emit("✅计算完成")

            self.custom_after_all_cal_signal.emit({
                "files_map": files_map
            })


class MyMonthlyEastDataClient(WindowWithMainWorker):
    """
    """

    help_info_text = """
=========== 场景描述 ===========
上传核心团险数据表和关联方名称以及名称代码表，计算
1. 农行和其他关联方的数据
2. 根据保险单号做groupby，的到其他列
3. 和important中之前计算的结果进行合并
每个月做一次

=========== Important文件 ===========
❗📗保险业务和其他类关联交易协议模板.xlsx
    保存内容模板，每次需要复制填数
    注意生成的文件格式：保险业务和其他类关联交易协议模板（202506农行员福+其他关联方）.xlsx

❗🔧config.json
    使用方式：使用过程中的配置文件，自动记录，无需手动管理
        记录配置的需要忽略的险种代码

=========== 系统配置文件 ===========
❗🔧auth.json
    在data根路径下
    使用方式：{"liwenxuan_0112@126.com": "token"} 的方式进行记录

=========== 注意事项 ===========
1. 上传的三个文件，除核心团险数据表外，其他excel文件没有列名
2. 自动进行区分：
    核心团险数据表：超过2列
    名称代码映射表：2列（没有列名，第一列是名称）
    名称表：1列（没有列名，第一列是名称）
3. 
    """

    release_info_text = """
v1.1.4 完成该场景
- 配置、上传
- 计算、融合
- 指定月份下载、发送
    """

    def __init__(self):
        """
        重要变量
            omit_baoxian_code_text：配置忽略险种代码规则的text
            target_year_text：默认是上个月对应的年份
            upload_button：上传文件按钮
                支持上传一个或多个核心团险数据excel，以及0个或1个内勤外勤人员统计
            cal_button：计算按钮
            download_file_button：下载文件按钮
                需要选定一个指定的月份，再下载
            send_file_button：发送文件按钮
            reset_button: 重置当前内容的button

            upload_info_text：上传后显示的汇总信息
                默认为空
            file_list：将计算完成的文件列出

        刚打开的时候
            1. 设置上月对应的年份到：target_year_text
            2. 将important中上次计算的月份，在 upload_list 列出
                1月（待计算）
                2月（已计算）
        """
        super(MyMonthlyEastDataClient, self).__init__()
        uic.loadUi(UI_PATH.format(file="monthly_east_data.ui"), self)  # 加载.ui文件
        self.setWindowTitle("每月east数据汇总计算——By LWX")
        self.tip_loading = self.modal(level="loading", titile="加载中...", msg=None)
        # 初始化帮助信息
        self.help_info_button.clicked.connect(
            lambda: self.modal(level="info", msg=self.help_info_text, width=800, height=400))
        self.release_info_button.clicked.connect(lambda: self.modal(level="info", msg=self.release_info_text))

        # 设置默认的保险代码配置
        try:
            with open(CONFIG_PATH) as f:
                self.config = json.loads(f.read())
        except Exception:
            self.config = {"omit_baoxian_code": "7824,2801,7854"}
            with open(CONFIG_PATH, "w") as f:
                f.write(json.dumps(self.config))
        # todo: 计算时这个config没有保存每次都要重新做（同业交流那里也是）

        # 设置上个月的年份
        target_year = TimeObj().year_of_last_month
        self.target_year_text.setText(str(target_year))

        # 上传文件按钮
        self.upload_button.clicked.connect(self.upload_files_action)
        # 计算按钮
        self.cal_button.clicked.connect(self.cal_baoxian_action)
        # 下载文件按钮
        self.download_file_button.clicked.connect(self.download_file_action)
        # 发送邮件按钮
        self.send_file_button.clicked.connect(self.send_file_action)
        # 重置按钮
        self.reset_button.clicked.connect(self.reset_all_action)
        # 展示上传文件结果
        self.file_list_wrapper = ListWidgetWrapper(self.file_list)
        #
        self.upload_file_path_map = None  # 上传的结果 dict，{"核心团险数据": "", "名称": "", "名称代码映射": ""}
        self.finish_file_name = None  # 计算的结果文件名


    def register_worker(self):
        return Worker()

    def upload_files_action(self):
        file_names = self.upload_file_modal(["Excel Files", "*.xls*"], multi=True)
        if not file_names:
            return

        params = {
            "stage": "check_upload",
            "file_path_list": file_names,
        }
        self.worker.add_params(params).start()

        # 增加loading tip
        self.tip_loading.set_titles(["上传文件校验.", "上传文件校验..", "上传文件校验..."]).show()

        pass

    def custom_after_check_upload(self, result):
        is_success = result.get("is_success")
        error_msg = result.get("error_msg")
        upload_file_path_map = result.get("upload_file_path_map")  # {"核心团险数据": "", "名称": "", "名称代码映射": ""}
        self.tip_loading.hide()

        # 校验是否通过
        if not is_success:
            self.modal(level="warn", msg=error_msg)
            return

        file_list = []  # todo: 获取历史上做完的结果，拼上这次要做的
        self.upload_list_wrapper.fill_data_with_color(
            file_list
        )
        self.upload_file_path_map = upload_file_path_map

    def cal_baoxian_action(self):
        if self.upload_file_path_map is None:
            self.modal(level="warn", msg="请先上传核心团险数据、名称表、名称代码映射表")
            return

        # 发起计算任务
        params = {
            "stage": "start_cal",
            "upload_file_path_map": self.upload_file_path_map,
            "target_year": self.target_year_text.text(),
            "omit_baoxian_code": [i.strip() for i in self.omit_baoxian_code_text.text().split(",")],
        }
        self.worker.add_params(params).start()

        # 增加loading tip
        self.tip_loading.set_titles(["计算.", "计算..", "计算..."]).show()

    def custom_after_one_cal(self, result):
        pass
    #     self.done_num += 1
    #     month = result.get("month")
    #     self.upload_list_wrapper.set_text_by_index(month - 1,
    #                                                f"{CALED_FILE.format(month=month)}（{round(time.time() - self.last_run_time, 2)}s）")
    #     need_cal = len(self.upload_info.upload_tuanxian_month_dict)
    #     new_text = f"当前年份：{self.upload_info.year}，汇总计算 {self.done_num}/{need_cal}个月度数据，平均耗时{round((time.time() - self.start_run_time) / self.done_num, 2)}s"
    #     self.upload_info_text.setText(new_text)
    #     self.last_run_time = time.time()

    def custom_after_all_cal(self, result):
        self.tip_loading.hide()
        self.finish_file_name = result.get("finish_file_name")
        file = self.finish_file_name
        index = self.file_list_wrapper.get_text_by_index(file)
        self.file_list_wrapper.set_text_by_index(index, "✅" + file)

    def download_file_action(self):
        if self.finish_file_name is None:
            self.modal(level="warn", msg="请先计算")
            return
        selected = self.upload_list_wrapper.get_selected_text()
        if selected:
            file = selected[0]
            if "✅" not in file:
                self.modal(level="warn", msg="文件未计算完成，无法下载")
                return
        else:
            file = self.upload_list_wrapper.get_text_by_index(-1)
        file = file.strip("✅")
        file_path = os.path.join(IMPORTANT_PATH, file)
        target_file_path = self.download_file_modal(file)
        copy_file(file_path, target_file_path)
        self.modal(level="info", msg="✅下载成功")

    def send_file_action(self):
        selected = self.upload_list_wrapper.get_selected_text()
        if selected:
            file = selected[0]
            if "✅" not in file:
                self.modal(level="warn", msg="文件未计算完成，无法发送")
                return
        else:
            file = self.upload_list_wrapper.get_text_by_index(-1)
        file = file.strip("✅")
        file_path = os.path.join(IMPORTANT_PATH, file)

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

    def reset_all_action(self):
        self.file_list_wrapper.clear()  # 上传的list

        self.upload_file_path_map = None  # 上传的结果 dict，{"核心团险数据": "", "名称": "", "名称代码映射": ""}
        self.finish_file_name = None  # 计算的结果文件名

        self.modal("info", title="Success", msg="重置成功")

