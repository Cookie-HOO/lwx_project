import time

import pandas as pd
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal

from lwx_project.client.base import BaseWorker, WindowWithMainWorker
from lwx_project.client.const import UI_PATH
from lwx_project.client.utils.list_widget import ListWidgetWrapper
from lwx_project.client.utils.table_widget import TableWidgetWrapper
from lwx_project.scene import product_name_match
from lwx_project.scene.product_name_match.const import *

from lwx_project.utils.conf import set_txt_conf, get_txt_conf
from lwx_project.utils.excel_checker import ExcelCheckerWrapper
from lwx_project.utils.excel_style import ExcelStyleValue
from lwx_project.utils.file import get_file_name_without_extension


UPLOAD_REQUIRED_FILES = ["需匹配的产品"]  # 上传的文件必须要有


class Worker(BaseWorker):
    custom_set_product_name_match_signal = pyqtSignal(pd.DataFrame)  # 自定义信号

    def __init__(self):
        super().__init__()
        self.df_text = None
        self.df_value = None

    def my_run(self):
        self.refresh_signal.emit("匹配中...")
        df_product = self.get_param("df_product")
        df_match_list = self.get_param("df_match_list")
        match_years = self.get_param("match_years")
        
        df_result = product_name_match.main(df_product, df_match_list, match_years)
        self.custom_set_product_name_match_signal.emit(df_result)


class MyProductNameMatchClient(WindowWithMainWorker):
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
        super(MyProductNameMatchClient, self).__init__()
        uic.loadUi(UI_PATH.format(file="product_name_match.ui"), self)  # 加载.ui文件
        self.setWindowTitle("产品名称匹配——By LWX")
        self.init_help_button(self.__doc__)

        # 0. 获取wrapper（组件转换）
        # 配置：匹配产品名称时不重要的内容
        self.product_name_match_unimportant_list_wrapper = ListWidgetWrapper(self.product_name_match_unimportant_list, add_rows_button=True, del_rows_button=True)
        # 上传文件展示：
        self.file_list_wrapper = ListWidgetWrapper(self.file_list)
        # 期数匹配展示
        self.product_name_match_table_wrapper = TableWidgetWrapper(self.product_name_match_table_value)

        # 1. 初始化
        # 1.1 读取系统配置文件
        self.init_file_config()  # 填充file_config到界面

        # 1.2 初始化高级配置的窗口
        self.config_dock.resize(600, 800)
        self.config_dock.hide()
        self.config_button.clicked.connect(lambda: self.config_dock.show())

        # # 2. checkbox绑定
        # self.only_has_fee_checkbox.stateChanged.connect(self.change_df_value)
        # self.only_no_product_name_checkbox.stateChanged.connect(self.change_df_value)

        # 3. 按钮绑定
        # 3.1 上传文件按钮的绑定
        self.upload_file_button.clicked.connect(self.upload_file)  # 将按钮的点击事件连接到upload_file方法
        # 3.2 执行按钮绑定

        self.df_product = None
        self.df_match_list = None
        self.match_years = None
        self.do_button.clicked.connect(self.do)
        # 3.3 下载文件按钮绑定
        self.df_result = None
        self.download_file_button.clicked.connect(lambda: self.download_zip_or_file_from_path(path_or_df=self.df_result, default_topic="匹配结果"))
        # 3.6 高级配置：保存匹配期数时不重要的内容
        self.save_product_name_match_unimportant_list_button.clicked.connect(
            lambda: self.func_modal_wrapper("保存成功", set_txt_conf, PRODUCT_MATCH_UNIMPORTANT_PATTERN_PATH,
                                            self.product_name_match_unimportant_list_wrapper.get_data_as_str())
        )
        # 3.8 重置按钮
        self.reset_button.clicked.connect(self.reset)

    def register_worker(self):
        return Worker()

    def init_file_config(self):
        # 界面配置初始化
        if not self.is_empty_status:
            return self.modal("warn", msg="系统异常")
        self.product_name_match_unimportant_list_wrapper.fill_data_with_color(get_txt_conf(PRODUCT_MATCH_UNIMPORTANT_PATTERN_PATH, list), editable=True)

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
        )
        if not file_names:
            return

        # 上传的文件是
        # 1. 需匹配的产品.xlsx
        # 2. 一批待匹配的文件
        df_product_path = [i for i in file_names if i.endswith("需匹配的产品.xlsx")][0]
        df_list_path = [i for i in file_names if not i.endswith("需匹配的产品.xlsx")]

        # 上传文件的校验
        product_excel_checker = ExcelCheckerWrapper(excel_path=df_product_path).has_cols(["产品名称", "公司名称"])
        if product_excel_checker.check_any_failed():
            return self.modal("warn", f"文件校验失败：{product_excel_checker.reason}")
        df_product = product_excel_checker.df[["产品名称", "公司名称"]]

        self.modal("tip", f"文件即将开始校验，校验过程耗时可能较久，请耐心等待")

        df_match_list = []
        match_years = []
        start = time.time()
        for path in df_list_path:
            match_excel_checker = ExcelCheckerWrapper(excel_path=path, skiprows=2).has_cols(["险种名称"])
            if match_excel_checker.check_any_failed():
                return self.modal("warn", f"文件校验失败：{match_excel_checker.reason}")
            df_match_list.append(match_excel_checker.df[["险种名称"]])

            print("校验col", time.time()-start)

            # 日期：2015年01月01日--2015年12月31日    机构:总行    货币单位:万元    统计渠道:全部
            text = ExcelStyleValue(excel_path=path, run_mute=True).get_cell((2, 1))
            year: str = text.split("年")[0].split("：")[-1]
            if not year.isdigit():
                return self.modal("warn", f"文件校验失败：{path} 的第二行第1列没有年份")
            match_years.append(year)

            print("获取值", time.time() - start)

        self.modal(level="tip", msg="文件校验成功")

        # 设置状态
        base_names = [get_file_name_without_extension(file_name) for file_name in file_names]
        self.file_list_wrapper.fill_data_with_color(base_names)
        self.set_status_init()
        
        self.df_product = df_product
        self.df_match_list = df_match_list
        self.match_years = match_years

    def do(self):
        """核心执行函数
        :return:
        """
        if self.is_running:
            return self.modal("warn", msg="程序执行中,请不要重新执行", done=True)
        elif not self.is_init:
            return self.modal("warn", msg="请先上传文件", done=True)

        self.product_name_match_table_wrapper.clear()

        params = {
            "df_product": self.df_product,  # 要匹配的产品名称
            "df_match_list": self.df_match_list,  # 各年的产品名称
            "match_years": self.match_years,  # 年份匹配
            # "run_mute_checkbox": self.run_mute_checkbox.isChecked(),  # 是否静默执行
        }

        self.worker.add_params(params).start()

    def custom_set_product_name_match(self, df_value: pd.DataFrame):
        """接受跑出来的df_value"""
        self.df_result = df_value
        self.product_name_match_table_wrapper.fill_data_with_color(
            df_value,
        )

    def reset(self):
        if self.is_running:
            return self.modal(level="warn", msg="运行中，无法重置，请等待执行完成")
        self.product_name_match_table_wrapper.clear()
        self.set_status_empty()
        self.status_text = ""
        self.modal("info", title="Success", msg="重置成功")

