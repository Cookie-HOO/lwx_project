import json
import os

from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal

from lwx_project.client.base import BaseWorker, WindowWithMainWorker
from lwx_project.client.const import UI_PATH
from lwx_project.client.utils.list_widget import ListWidgetWrapper
from lwx_project.client.utils.table_widget import TableWidgetWrapper
from lwx_project.scene.monthly_communication_data.cal_excel import cal_and_merge
from lwx_project.scene.monthly_communication_data.check_excel import check_excels, UploadInfo
from lwx_project.scene.monthly_communication_data.const import CONFIG_PATH, IMPORTANT_PATH
from lwx_project.utils.file import copy_file


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
                upload_info = upload_info,
                code_rules_dict=code_rules_dict,
                after_one_done_callback=lambda index: None,
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
3. 和important中之前计算的结果
每个月做一次

=========== Important文件 ===========
❗📗模板.xlsx
    保存内容模板，每次需要复制填数

❗🔧config.json
    使用方式：使用过程中的配置文件，自动记录，无需手动管理
        记录配置的各种险种的计算规则

=========== 注意事项 ===========
1. 支持多个核心团险数据excel（根据列的情况自动识别是哪一个月的）
2. 每次执行会保存这次执行的配置
3. 下载文件时需要指定某一个月的汇总结果进行下载
    """

    release_info_text = """
v1.1.2: 完成该场景
- 配置险种、上传
- 计算、融合
- 指定月份下载
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
        self.init_important_caled_month()  # 初始化上次计算完的月份

        # 配置保险代码规则的table
        self.baoxian_code_config_table_wrapper = TableWidgetWrapper(self.baoxian_code_config_table)

        # 上传文件按钮
        self.upload_button.clicked.connect(self.upload_files_action)
        # 计算按钮
        self.cal_button.clicked.connect(self.cal_baoxian_action)
        # 下载文件按钮
        self.download_file_button.clicked.connect(self.download_file_action)
        # 重置按钮
        self.reset_button.clicked.connect(self.reset_all_action)
        # 展示上传文件结果
        self.upload_list_wrapper = ListWidgetWrapper(self.upload_list)

        self.upload_info = None  # 上传的结果
        self.result_files_map = None # 计算的结果

    def register_worker(self):
        return Worker()

    def init_important_caled_month(self):
        # todo
        pass

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
            # return TODO

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
        self.upload_list_wrapper.fill_data_with_color(
            [f"{i}月核心团险数据" for i in need_cal_month_list]
        )
        self.upload_info = upload_info
        # todo


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


        # 发起计算任务
        params = {
            "stage": "start_cal",
            "upload_info": self.upload_info,
            "code_rules_dict": code_rules_dict,
        }
        self.worker.add_params(params).start()

        # 增加loading tip
        self.tip_loading.set_titles(["计算.", "计算..", "计算..."]).show()
    def custom_after_one_cal(self, result):
        # self.tip_loading.hide()
        pass

    def custom_after_all_cal(self, result):
        self.tip_loading.hide()
        self.result_files_map = result.get("files_map")
        self.upload_list_wrapper.clear()
        self.upload_list_wrapper.fill_data_with_color(
            self.result_files_map.keys()
        )


    def download_file_action(self):
        selected = self.upload_list_wrapper.get_selected_text()
        if selected:
            file = selected[0]
        else:
            file = self.upload_list_wrapper.get_text_by_index(-1)
        file_path = os.path.join(IMPORTANT_PATH, str(self.upload_info.year), file)
        target_file_path = self.download_file_modal(file)
        copy_file(file_path, target_file_path)
        self.modal(level="info", msg="✅下载成功")


    def reset_all_action(self):
        self.upload_list_wrapper.clear()  # 上传的list

        self.upload_info = None  # 上传的结果
        self.caled_path = None # 计算的结果

        self.modal("info", title="Success", msg="重置成功")

