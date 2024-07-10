import pandas as pd
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QComboBox

from lwx_project.client.base import BaseWorker, WindowWithMainWorker
from lwx_project.client.const import UI_PATH, COLOR_RED
from lwx_project.client.utils.list_widget import ListWidgetWrapper
from lwx_project.client.utils.table_widget import TableWidgetWrapper
from lwx_project.scene.product_evaluation.const import *
from lwx_project.scene.product_evaluation.steps import data_preprocess, get_text, get_value, split_sheet
from lwx_project.utils.conf import set_csv_conf, set_txt_conf, get_csv_conf, get_txt_conf, CSVConf
from lwx_project.utils.excel_checker import ExcelCheckerWrapper
from lwx_project.utils.file import get_file_name_without_extension
from lwx_project.utils.my_itertools import dedup_list
from lwx_project.utils.strings import replace_parentheses_and_comma
from lwx_project.utils.time_obj import TimeObj

UPLOAD_REQUIRED_FILES = ["产品目录", "分行代理保险产品分险种销售情况统计表", "对应表", "上期保费"]  # 上传的文件必须要有

OFFICER_COMPANY_CONF = CSVConf(OFFICER_COMPANY_PATH, init_columns=["公司", "人员"])
TERM_PAIR_CONF = CSVConf(TERM_MATCH_PAIR_PATH, init_columns=["产品", "期数"])


class Worker(BaseWorker):
    custom_set_term_match_signal = pyqtSignal(pd.DataFrame)  # 自定义信号

    def __init__(self):
        super().__init__()
        self.df_text = None
        self.df_value = None

    def my_run(self):
        stage = self.get_param("stage")  # self.equal_buffer_value.value()
        if stage == "1":  # 任务处在第一阶段，说明需要执行预处理和获取文本以及获取数值的操作
            # 第一步：数据预处理：删除无效数据 + 匹配简称
            self.refresh_signal.emit("1. 数据预处理...")
            df = data_preprocess.main()

            # 第二步：获取文本
            self.refresh_signal.emit("2. 获取评价文本...")
            self.df_text = get_text.main(df)

            # 第三步：预处理期数
            self.refresh_signal.emit("3. 预处理期数...")
            self.df_value = get_value.main(df)
            self.custom_set_term_match_signal.emit(self.df_value)
        elif stage == "2":  # 任务处在第二阶段，说明用户指定完期数，并点击了继续执行
            # 第四步：excel拆分
            new_df_value = self.get_param("new_df_value")  # 需要window在获取用户修改的df_value后设置过来
            officer_list = self.get_param("officer_list")  # 需要window在获取用户修改的df_value后设置过来
            if self.df_text is None or new_df_value is None:
                return self.modal_signal.emit("error", msg="没有文本或者值")
            self.refresh_signal.emit("4. 拆分excel...")
            for index, officer in enumerate(officer_list):
                self.refresh_signal.emit(f"4. 拆分excel... {officer}:: {index+1}/{len(officer_list)}")
                split_sheet.main(self.df_text, new_df_value, officer=officer)


class MyProductEvaluationClient(WindowWithMainWorker):
    """
    重要变量
        config_button: 高级配置按钮
            点击后展示高级配置
        company_officer_table_value: 配置：展示公司人员的映射关系，是一个table   company -> officer
            save_company_officer_table_button
        term_match_unimportant_list_value: 配置：期数匹配中可以删除的内容，是一个text
            save_term_match_unimportant_list_button

        upload_file_button: 上传文件的按钮，上传文件后，将文件名和对应的时间展示在 file_date_value 这里
        do_button: 点击后进行执行
        run_mute_checkbox: 静默执行的checkbox

        file_list_title：最开始设置为上传的文件，后面设置为下载的文件
        file_list: 展示上传的文件（tmp路径下的文件）
        only_has_fee_checkbox: 只展示有保费
        only_no_term_checkbox：只展示没有匹配的
        term_match_table_value: 展示期数：公司、期数、匹配公司及期数、提示原因
            1. 有问题的用红色标识出来
            2. 第二列期数是一个下拉选择框
        confirm_term_button：当用户点击确认期数之后，进行弹窗提示，再次确认后执行下一阶段

        download_file_button: 下载最终文件的按钮
            拆分后的所有excel
        reset_button: 重置当前内容的button
    """

    def __init__(self):
        super(MyProductEvaluationClient, self).__init__()
        uic.loadUi(UI_PATH.format(file="product_evaluation.ui"), self)  # 加载.ui文件
        self.setWindowTitle("产品评估——By LWX")

        # 0. 获取wrapper（组件转换） todo 后续考虑在基类中自动转
        # 配置：公司人员映射的wrapper
        self.company_officer_table_wrapper = TableWidgetWrapper(self.company_officer_table_value, add_rows_button=True, del_rows_button=True)
        # 配置：匹配期数时不重要的内容
        self.term_match_unimportant_list_wrapper = ListWidgetWrapper(self.term_match_unimportant_list, add_rows_button=True, del_rows_button=True)
        # 上传文件展示：
        self.file_list_wrapper = ListWidgetWrapper(self.file_list)
        # 期数匹配展示
        self.term_match_table_wrapper = TableWidgetWrapper(self.term_match_table_value)

        # 1. 初始化
        # 1.1 读取系统配置文件
        self.init_file_config()  # 填充file_config到界面

        # 1.2 初始化高级配置的窗口
        self.config_dock.resize(600, 800)
        self.config_dock.hide()
        self.config_button.clicked.connect(lambda: self.config_dock.show())

        # 2. checkbox绑定
        self.only_has_fee_checkbox.stateChanged.connect(self.change_df_value)
        self.only_no_term_checkbox.stateChanged.connect(self.change_df_value)

        # 3. 按钮绑定
        # 3.1 上传文件按钮的绑定
        self.upload_file_button.clicked.connect(self.upload_file)  # 将按钮的点击事件连接到upload_file方法
        # 3.2 执行按钮绑定
        self.df_value = None
        self.do_button.clicked.connect(self.do)
        # 3.3 下载文件按钮绑定
        self.download_file_button.clicked.connect(lambda: self.download_zip_from_path(path=DATA_TMP_PATH, default_topic="产品评估"))
        # 3.4 高级配置：保存公司人员映射
        self.save_company_officer_table_button.clicked.connect(
            lambda: self.func_modal_wrapper("保存成功", set_csv_conf, OFFICER_COMPANY_PATH,
                                            self.company_officer_table_wrapper.get_data_as_df()))
        # 3.6 高级配置：保存匹配期数时不重要的内容
        self.save_term_match_unimportant_list_button.clicked.connect(
            lambda: self.func_modal_wrapper("保存成功", set_txt_conf, TERM_MATCH_UNIMPORTANT_PATTERN_PATH,
                                            self.term_match_unimportant_list_wrapper.get_data_as_str())
        )

        # 3.7 期数确认按钮
        self.confirm_term_button.clicked.connect(self.continue_do)

        # 3.8 重置按钮
        self.reset_button.clicked.connect(self.reset)

    def register_worker(self):
        return Worker()

    def init_file_config(self):
        # 界面配置初始化
        if not self.is_empty_status:
            return self.modal("warn", msg="系统异常")
        self.company_officer_table_wrapper.fill_data_with_color(get_csv_conf(OFFICER_COMPANY_PATH))
        self.term_match_unimportant_list_wrapper.fill_data_with_color(get_txt_conf(TERM_MATCH_UNIMPORTANT_PATTERN_PATH, list), editable=True)
        if TimeObj().season == 2:  # 第二季度需要清空期数匹配文件
            TERM_PAIR_CONF.clear()

    def upload_file(self):
        """上传文件
        :return:
        """
        if self.is_init:
            return self.modal("warn", msg="已经上传过了, 请先重置")
        elif self.is_running:
            return self.modal("warn", msg="正在运行中, 禁止操作")
        elif self.is_done:
            return self.modal("warn", msg="已完成,下次使用前请先重置")

        file_names = self.upload_file_modal(
            ["Excel Files", "*.xls*"],
            multi=True,
            required_base_name_list=UPLOAD_REQUIRED_FILES,
            copy_to=DATA_TMP_PATH,
        )
        if not file_names:
            return

        # 上传文件校验
        # 1. 对应表的实际简称校验
        #    不能重复 | 公司人员表中的公司都在 实际简称 的列中
        """
        PRODUCT_LIST_PATH = os.path.join(DATA_TMP_PATH, "产品目录.xlsx")
        PRODUCT_DETAIL_PATH = os.path.join(DATA_TMP_PATH, "分行代理保险产品分险种销售情况统计表.xlsx")
        COMPANY_ABBR_PATH = os.path.join(DATA_TMP_PATH, "对应表.xlsx")
        LAST_TERM_PATH = os.path.join(DATA_TMP_PATH, "上期保费.xlsx")
        """
        # 对应表
        condition = ExcelCheckerWrapper(COMPANY_ABBR_PATH)\
            .has_cols(cols=["全称", "实际简称", "产品目录统计"])\
            .has_values(col="实际简称", values=OFFICER_COMPANY_CONF.get()["公司"].to_list())\
            .no_dup_values(col="实际简称")
        if condition.check_any_failed():
            return self.modal("warn", f"文件校验失败：{condition.reason}")

        # 产品目录
        condition = ExcelCheckerWrapper(PRODUCT_LIST_PATH)\
            .has_sheets(sheets=["银保", "私行", "个人养老金", "团险", "统计"])\
            .reset(sheet_name_or_index="统计")\
            .has_values(row=0, values=["公司全称", "银保产品", "私行产品", "团险", "公司小计"])\
            .has_values(row=1, values=["银保小计", "私行小计"])\
            .reset(sheet_name_or_index="银保") \
            .has_values(row=0, values=["产品名称", "期数"]) \
            .reset(sheet_name_or_index="私行") \
            .has_values(row=0, values=["产品名称", "期数"]) \
            .reset(sheet_name_or_index="个人养老金") \
            .has_values(row=0, values=["产品名称", "期数"])
        if condition.check_any_failed():
            return self.modal("warn", f"文件校验失败：{condition.reason}")

        # 分行代理保险产品分险种销售情况统计表
        condition = ExcelCheckerWrapper(PRODUCT_DETAIL_PATH) \
            .has_cols(["保险公司", "本期实现保费", "公司代码", "险种代码", "保险责任分类", "保险责任子分类", "保险期限", "缴费期间", "总笔数", "犹撤保费", "退保保费", "本期实现手续费收入"])
        if condition.check_any_failed():
            return self.modal("warn", f"文件校验失败：{condition.reason}")

        # 上期保费
        condition = ExcelCheckerWrapper(LAST_TERM_PATH) \
            .has_values(row=1, values=["险种名称", "本期实现保费"])
        if condition.check_any_failed():
            return self.modal("warn", f"文件校验失败：{condition.reason}")

        self.modal(level="tip", msg="文件校验成功")

        # 2. 设置状态
        base_names = [get_file_name_without_extension(file_name) for file_name in file_names]
        self.file_list_wrapper.fill_data_with_color(base_names)
        self.set_status_init()

    def do(self):
        """核心执行函数
        :return:
        """
        if self.is_running:
            return self.modal("warn", msg="程序执行中,请不要重新执行", done=True)
        elif not self.is_init:
            return self.modal("warn", msg="请先上传文件", done=True)

        self.term_match_table_wrapper.clear()

        params = {
            "stage": "1",  # 第一阶段
            "run_mute_checkbox": self.run_mute_checkbox.isChecked(),  # 是否静默执行
        }

        self.worker.add_params(params).start()

    def change_df_value(self):
        self.custom_set_term_match(self.df_value, call_from_worker=False)

    def custom_set_term_match(self, df_value: pd.DataFrame, call_from_worker=True):
        """接受跑出来的df_value"""
        self.df_value = df_value.copy()
        df_value = df_value[["险种名称", "保险公司", "保险类型", "保费", "期数"]]
        only_has_fee_df = df_value[df_value["保险类型"] == "有保费"]
        only_no_term_df = df_value[df_value["期数"] == EMPTY_TERM_PLACE_HOLDER]
        # 如果从worker中调用，展示个数
        if call_from_worker:
            self.only_has_fee_checkbox.setText(self.only_has_fee_checkbox.text() + f": {len(only_has_fee_df)}个")
            self.only_no_term_checkbox.setText(self.only_no_term_checkbox.text() + f": {len(only_no_term_df)}个")

        if self.only_has_fee_checkbox.isChecked():
            df_value = df_value[df_value["保险类型"] == "有保费"]
        if self.only_no_term_checkbox.isChecked():
            df_value = df_value[df_value["期数"] == EMPTY_TERM_PLACE_HOLDER]

        def cell_style_func(df_: pd.DataFrame, i, j):
            if df_.iloc[i, 4] == EMPTY_TERM_PLACE_HOLDER:
                return COLOR_RED

        def cell_widget_func(df_: pd.DataFrame, i, j):
            if df_.iloc[i, j] == EMPTY_TERM_PLACE_HOLDER:
                combo_box = QComboBox()
                combo_box.addItem(f"{EMPTY_TERM_PLACE_HOLDER}（未找到）")
                for i in [
                    "一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
                    "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十"
                ]:
                    combo_box.addItem(i)
                return combo_box

        self.term_match_table_wrapper.fill_data_with_color(
            df_value,
            cell_style_func=cell_style_func,
            cell_widget_func=cell_widget_func,
        )

    def continue_do(self):
        """确认期数后继续执行"""
        if self.df_value is None:
            return self.modal("warn", msg="请先执行")
        check_yes = self.modal("check_yes", msg="确认以此期数结果执行下一步吗")
        if not check_yes:
            return

        new_df_value = self.term_match_table_wrapper.get_data_as_df().rename(columns={"期数": "新期数"})[["新期数", "险种名称"]]
        merged = pd.merge(self.df_value.copy(), new_df_value.copy(), on="险种名称", how="left")
        merged['期数'] = merged['新期数'].fillna(merged['期数']).apply(lambda x: str(x).split("（")[0])  # —（未找到）
        params = {
            "stage": "2",  # 第二阶段
            "new_df_value": merged,
            "officer_list": dedup_list(get_csv_conf(OFFICER_COMPANY_PATH)["人员"].to_list()),
        }
        new_df_value["险种名称"] = new_df_value["险种名称"].apply(replace_parentheses_and_comma)
        TERM_PAIR_CONF.append(new_df_value.rename(columns={"新期数": "期数", "险种名称": "产品"})).dedup().save()
        self.worker.add_params(params).start()

    def reset(self):
        if self.is_running:
            return self.modal(level="warn", msg="运行中，无法重置，请等待执行完成")
        self.term_match_table_wrapper.clear()
        self.set_status_empty()
        self.status_text = ""
        self.modal("info", title="Success", msg="重置成功")

