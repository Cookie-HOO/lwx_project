import json
import os
import time
import typing

from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal

from lwx_project.client.base import BaseWorker, WindowWithMainWorker
from lwx_project.client.const import UI_PATH
from lwx_project.client.utils.list_widget import ListWidgetWrapper
from lwx_project.client.utils.table_widget import TableWidgetWrapper
from lwx_project.scene.monthly_communication_data.check_excel import check_excels, UploadInfo
from lwx_project.scene.monthly_communication_data.const import CONFIG_PATH, IMPORTANT_PATH, BEFORE_CAL_FILE, CALED_FILE
from lwx_project.scene.monthly_communication_data.main import cal_and_merge
from lwx_project.utils.file import copy_file, get_file_name_with_extension, open_file_or_folder
from lwx_project.utils.mail import send_mail


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
            self.refresh_signal.emit("计算中...")
            upload_info: UploadInfo = self.get_param("upload_info")
            code_rules_dict = self.get_param("code_rules_dict")

            files_map = cal_and_merge(
                upload_info = upload_info,
                code_rules_dict=code_rules_dict,
                after_one_done_callback=lambda month: self.custom_after_one_cal_signal.emit({
                    "month": month
                }),
            )
            self.refresh_signal.emit("✅计算完成")

            self.custom_after_all_cal_signal.emit({
                "files_map": files_map
            })


class MyMonthlyCommunicationDataClient(WindowWithMainWorker):
    """
    """

    help_info_text = """
=========== 场景描述 ===========
上传多个核心团险数据和内勤外勤人员统计，生成同业交流数据汇总
1. 上传多个核心团险数据
2. 根据分公司做groupby，计算各种险种的金额
3. 和important中之前计算的结果进行合并
每个月做一次

=========== Important文件 ===========
❗📗模板.xlsx
    保存内容模板，每次需要复制填数

❗🔧config.json
    使用方式：使用过程中的配置文件，自动记录，无需手动管理
        记录配置的各种险种的计算规则
        
=========== 系统配置文件 ===========
❗🔧auth.json
    在data根路径下
    使用方式：{"liwenxuan_0112@126.com": "token"} 的方式进行记录
    
=========== 注意事项 ===========
1. 支持多个核心团险数据excel（根据列的情况自动识别是哪一个月的）
2. 每次执行会保存这次执行的配置
3. 下载文件时需要指定某一个月的汇总结果进行下载
4. 在important目录下，按照年份进行文件夹分类管理
    """

    release_info_text = """
v1.1.2: 完成该场景
- 配置险种、上传
- 计算、融合
- 指定月份下载

v1.1.3: 
- feat: 增加发送邮件
- fix: 校验上传文件的问题
- update: auth.json的路径修改

v1.1.4
- update: 双击打开文件
- update: 执行中展示优化 🏃✅
    """

    def __init__(self):
        """
        重要变量
            baoxian_code_config_table：配置险种代码规则的table，共三列说明如下
                险种代码开头标记：不可编辑
                新增险种代码：
                忽略险种代码

                这三列分别对应：
                    意外险、健康险、医疗基金、年金险
            upload_button：上传文件按钮
                支持上传一个或多个核心团险数据excel，以及0个或1个内勤外勤人员统计
            cal_button：计算按钮
            download_file_button：下载文件按钮
                需要选定一个指定的月份，再下载
            upload_info_text：上传后显示的汇总信息
                当前年份：--，汇总计算 --/--个月度数据，合并结果 --/--个
            upload_list：上传后将相关的文件列出
            reset_button: 重置当前内容的button

        刚打开的时候
            1. 恢复上次执行时保存的险种配置
            2. 将important中上次计算的月份，在 upload_list 列出
                1月（待计算）
                2月（已计算）
        """
        super(MyMonthlyCommunicationDataClient, self).__init__()
        uic.loadUi(UI_PATH.format(file="monthly_communication_data.ui"), self)  # 加载.ui文件
        self.setWindowTitle("每月同业交流数据汇总计算——By LWX")
        self.tip_loading = self.modal(level="loading", titile="加载中...", msg=None)
        # 初始化帮助信息
        self.help_info_button.clicked.connect(lambda: self.modal(level="info", msg=self.help_info_text, width=800, height=400))
        self.release_info_button.clicked.connect(lambda: self.modal(level="info", msg=self.release_info_text))

        # 设置默认的保险代码配置
        try:
            with open(CONFIG_PATH) as f:
                self.config = json.loads(f.read())
        except Exception:
            self.config = {"baoxian_code_rule": {
                "意外险": [],
                "健康险": [-7824, -7854],  # 后面可能动态变
                "寿险": [],
                "医疗基金": [+7824, +7854],  # 后面可能动态变
                "年金险": [-2801],
            }}
            with open(CONFIG_PATH, "w") as f:
                f.write(json.dumps(self.config))
        # 配置保险代码规则的table
        self.baoxian_code_config_table_wrapper = TableWidgetWrapper(self.baoxian_code_config_table)

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
        self.upload_list_wrapper = ListWidgetWrapper(self.upload_list).bind_double_click_func(self.double_click_to_open)

        self.upload_info: typing.Optional[UploadInfo] = None  # 上传的结果
        self.done_num = 0
        self.last_run_time = None
        self.start_run_time = None

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
        upload_info: UploadInfo= result.get("res")
        self.tip_loading.hide()

        # 校验是否通过
        if not is_success:
            self.modal(level="warn", msg=error_msg)
            return

        # 设置上传信息
        # 1. 当前年份（上传的文件中共同的年份）
        # 2. 需要计算的个数（上传的核心团险数据的个数）
        # 当前年份：--，汇总计算 --/--个月度数据
        year = upload_info.year
        need_cal = len(upload_info.upload_tuanxian_month_dict)

        new_text = f"当前年份：{year}，汇总计算 --/{need_cal}个月度数据"
        self.upload_info_text.setText(new_text)

        # 设置上传结果
        need_cal_month_list = sorted(upload_info.upload_tuanxian_month_dict.keys())
        caled_month_list = sorted(upload_info.important_month_dict.keys())
        file_list = []
        for i in range(1, 13):
            if i not in need_cal_month_list+caled_month_list:
                break
            if i in need_cal_month_list:
                file_list.append(BEFORE_CAL_FILE.format(month=i))
            elif i in caled_month_list:
                file_list.append(f"✅{get_file_name_with_extension(upload_info.important_month_dict.get(i))}")

        self.upload_list_wrapper.fill_data_with_color(
            file_list
        )
        self.upload_info = upload_info

    def cal_baoxian_action(self):
        if self.upload_info is None:
            self.modal(level="warn", msg="请先上传核心团险数据文件")
            return
        # 整理当前规则
        """
        baoxian_code_config_table：配置险种代码规则的table，共三列说明如下
            险种代码开头标记：不可编辑
            新增险种代码：
            忽略险种代码
        """
        code_rules = self.baoxian_code_config_table_wrapper.get_data_as_df()

        def get_specific_rule(df, index):
            new_str = str(df["新增险种代码"][index]).strip()
            new = []
            if new_str:
                new = new_str.split(",")
            omit_str = df["忽略险种代码"][index].strip()
            new_int = [int(i.strip()) for i in new]

            omit = []
            if omit_str:
                omit = omit_str.split(",")
            omit_int = [int("-"+i.strip()) for i in omit]
            return new_int+omit_int

        code_rules_dict = {
            "意外险": get_specific_rule(code_rules, 0),
            "健康险": get_specific_rule(code_rules, 1),
            "寿险": get_specific_rule(code_rules, 2),
            "医疗基金": get_specific_rule(code_rules, 3),
            "年金险": get_specific_rule(code_rules, 4),
        }
        # running
        upload_tuanxian_month_dict = self.upload_info.upload_tuanxian_month_dict.keys()
        this_index = sorted(upload_tuanxian_month_dict)[0] - 1  # 一定是从第一个月开始排的，所以算的月份-1，就是算的索引
        self.upload_list_wrapper.set_text_by_index(this_index, f"🏃{CALED_FILE.format(month=this_index + 1)}")

        # 发起计算任务
        params = {
            "stage": "start_cal",
            "upload_info": self.upload_info,
            "code_rules_dict": code_rules_dict,
        }
        self.worker.add_params(params).start()

        # 保存这次跑的配置
        self.config["baoxian_code_rule"] = code_rules_dict
        with open(CONFIG_PATH, "w") as f:
            f.write(json.dumps(self.config))

        # 记录开始时间
        self.last_run_time = time.time()
        self.start_run_time = self.last_run_time

        # 增加loading tip
        self.tip_loading.set_titles(["计算.", "计算..", "计算..."]).show()

    def custom_after_one_cal(self, result):
        self.done_num += 1
        month = result.get("month")
        self.upload_list_wrapper.set_text_by_index(month-1, f"✅{CALED_FILE.format(month=month)}\t{round(time.time()-self.last_run_time,2)}s")
        self.upload_list_wrapper.set_text_by_index(month, f"🏃{CALED_FILE.format(month=month+1)}")
        need_cal = len(self.upload_info.upload_tuanxian_month_dict)
        new_text = f"当前年份：{self.upload_info.year}，汇总计算 {self.done_num}/{need_cal}个月度数据，平均耗时{round((time.time()-self.start_run_time)/self.done_num,2)}s"
        self.upload_info_text.setText(new_text)
        self.last_run_time = time.time()


    def custom_after_all_cal(self, result):
        self.tip_loading.hide()

    def double_click_to_open(self, file_name):
        if self.upload_info is None or not file_name.startswith("✅"):
            self.modal(level="warn", msg="请等待执行完成后再打开")
            return
        file_name = file_name.split("\t")[0].strip("✅").strip()
        path = os.path.join(IMPORTANT_PATH, str(self.upload_info.year), file_name)
        open_file_or_folder(path)

    def download_file_action(self):
        selected = self.upload_list_wrapper.get_selected_text()
        if selected:
            file = selected[0]
        else:
            file = self.upload_list_wrapper.get_text_by_index(-1)
        if file is None:
            self.modal(level="warn", msg="没有可供下载的文件，请上传或执行")
            return
        file = file.split("\t")[0].strip("✅").strip()
        file_path = os.path.join(IMPORTANT_PATH, str(self.upload_info.year), file)
        target_file_path = self.download_file_modal(file)
        copy_file(file_path, target_file_path)
        self.modal(level="info", msg="✅下载成功")

    def send_file_action(self):
        selected = self.upload_list_wrapper.get_selected_text()
        if selected:
            file = selected[0]
        else:
            file = self.upload_list_wrapper.get_text_by_index(-1)
        if file is None:
            self.modal(level="warn", msg="没有可供下载的文件，请上传或执行")
            return
        file = file.split("\t")[0].strip("✅").strip()
        file_path = os.path.join(IMPORTANT_PATH, str(self.upload_info.year), file)

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
        self.upload_list_wrapper.clear()  # 上传的list

        self.upload_info = None  # 上传的结果
        self.done_num = 0
        self.last_run_time = None
        self.start_run_time = None

        self.modal("info", title="Success", msg="重置成功")

