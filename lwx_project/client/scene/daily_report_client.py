import json
import os.path
import random

from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QColor

from lwx_project.client.base import BaseWorker, WindowWithMainWorker
from lwx_project.client.const import UI_PATH, COLOR_RED, COLOR_GREEN, COLOR_WHITE
from lwx_project.client.utils.list_widget import fill_data
from lwx_project.scene.daily_report.const import *
from lwx_project.scene.daily_report.main import before_run, after_run
from lwx_project.scene.daily_report.steps import rename, calculate, sheet_picture
from lwx_project.utils.conf import get_txt_conf, set_txt_conf
from lwx_project.utils.file import get_file_name_without_extension, make_zip
from lwx_project.utils.time_obj import TimeObj

UPLOAD_REQUIRED_FILES = ["代理期缴保费", "公司网点经营情况统计表", "农行渠道实时业绩报表"]  # 上传的文件必须要有
UPLOAD_IMPORTANT_FILE = "每日报表汇总"  # 如果有会放到tmp路径下


class Worker(BaseWorker):
    custom_set_random_leader_word_signal = pyqtSignal(str, dict)  # 自定义信号

    def my_run(self):
        before_run()  # 清理路径

        # 第一步：重命名后显示修改的内容
        self.refresh_signal.emit("重命名...")
        equal_buffer_value = self.get_param("equal_buffer_value")  # self.equal_buffer_value.value()
        date_file_names = self.get_param("date_file_names")  # self.date_file_names
        important_file_names = self.get_param("important_file_names")  # self.important_file_names
        run_mute_checkbox = self.get_param("run_mute_checkbox")  # run_mute_checkbox.isChecked()

        if isinstance(equal_buffer_value, int) and equal_buffer_value >= 0:
            new_file_name2date_dict = rename.main(date_file_names, equal_buffer_value)
            # self.file_date_value.clear()
            # for key, value in self.new_file_name2date_dict.items():
            #     self.file_date_value.addItem(f'{key}: {value}')
            self.set_element_signal.emit("file_date_value", json.dumps([f'{key}: {value}' for key, value in new_file_name2date_dict.items()]))

        # 检查结果
        for file in KEY_RESULT_FILE_SET:
            if file not in os.listdir(DATA_TMP_PATH):
                return self.modal_signal.emit("error", f"缺少 {file} 文件，无法进行下一步")

        # 第二步：执行宏
        self.refresh_signal.emit("执行宏...")
        result = calculate.main(
            copy2tmp_path_list=important_file_names,
            run_mute=run_mute_checkbox,
        )

        self.custom_set_random_leader_word_signal.emit(result["num_text"], result["leader_word_variables"])

        # 第三步截图
        r = range(3, 14)
        for index, i in enumerate(r):  # 3,4,5...,13
            self.refresh_signal.emit(f"生成截图: {index+1}/{len(r)}")
            img_path = os.path.join(DATA_TMP_PATH, f"{i}.png")
            sheet_picture.main(
                excel_path=DAILY_REPORT_TMP_TEMPLATE_PATH,
                sheet_name_or_index=i,
                img_path=img_path,
                padding=[20, 20, 0, 20],  # up right bottom left
                run_mute=run_mute_checkbox
            )


class MyDailyReportClient(WindowWithMainWorker):
    """
    重要变量
        config_button: 高级配置按钮
            点击后展示高级配置
        leader_word_template_value: 展示 领导的话的模板
        save_leader_word_template_button: 保存 领导的话的模板
        motto_list_value: 展示所有的名言警句，需要找个地方保存，下次打开进行加载
        save_motto_list_button: 保存所有名言警句

        upload_file_button: 上传文件的按钮，上传文件后，将文件名和对应的时间展示在 file_date_value 这里
        equal_buffer_value: 判断当日相等的buffer
        do_button: 点击后进行执行
        run_mute_checkbox: 静默执行的checkbox

        file_date_value: 上传文件后显示文件名和对应的日期，点击执行后，这里替换成改完名字的内容和日期
        leader_word_value: 展示填充完名言警句的给领导的话，其中名言警句单独一行，可以被 motto_change_button 修改
        motto_change_button: 点击后快速闪烁名言警句4-7句后停止
        copy_summary_button: 点击后将领导的话复制到剪贴板

        download_file_button: 下载最终文件的按钮
            代理期缴保费.xlsm(传上来的，但是执行宏会改）
            每日报表汇总.xlsm(有可能传，执行完宏会变)
            改名的所有文件（改完名的xlsx）
            生成的图片（指定excel的范围，）
        reset_button: 重置当前内容的button
    """
    def __init__(self):
        super(MyDailyReportClient, self).__init__()
        uic.loadUi(UI_PATH.format(file="daily_report.ui"), self)  # 加载.ui文件
        self.setWindowTitle("日报——By LWX")

        # 读取系统配置文件
        self.init_file_config()  # 填充file_config到界面

        # 1. 初始化高级配置的窗口
        self.config_dock.resize(600, 800)
        self.config_dock.hide()
        self.config_button.clicked.connect(lambda: self.config_dock.show())

        # 2. 按钮绑定
        ## 2.1 上传文件按钮的绑定
        self.date_file_names = None
        self.important_file_names = None
        self.upload_file_button.clicked.connect(self.upload_file)  # 将按钮的点击事件连接到upload_file方法
        ## 2.2 执行按钮绑定
        self.num_text = ""
        self.leader_word_variables = {}
        self.do_button.clicked.connect(self.do)
        ## 2.3 随机生成名言警句按钮绑定
        self.motto_change_button.clicked.connect(lambda: self.modal_func_wrapper(self.is_success, "请先执行或等待完成" + self.status_text, self.custom_set_random_leader_word, self.num_text, self.leader_word_variables))
        ## 2.4 拷贝按钮绑定
        self.copy_summary_button.clicked.connect(lambda: self.copy2clipboard(self.leader_word_value.toPlainText()))
        ## 2.5 下载文件按钮绑定
        self.download_file_button.clicked.connect(self.download_file)
        ## 2.6 高级配置：保存领导的话按钮
        self.save_leader_word_template_button.clicked.connect(
            lambda: self.func_modal_wrapper("保存成功", set_txt_conf, LEADER_WORD_TEMPLATE_PATH,self.leader_word_template_value.toPlainText()))
        ## 2.7 高级配置：保存名言警句
        self.save_motto_list_button.clicked.connect(
            lambda: self.func_modal_wrapper("保存成功", set_txt_conf, MOTTO_TEXT_PATH, self.motto_list_value.toPlainText())
        )
        ## 2.8 重置按钮
        self.reset_button.clicked.connect(self.reset)

    def register_worker(self):
        return Worker()

    def init_file_config(self):
        # 界面配置初始化
        if not self.is_empty_status:
            return self.modal("warn", msg="系统异常")
        self.leader_word_template_value.setText(get_txt_conf(LEADER_WORD_TEMPLATE_PATH, str))
        self.motto_list_value.setText(get_txt_conf(MOTTO_TEXT_PATH, str))

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

        file_names = self.upload_file_modal(["Excel Files", "*.xls*"], multi=True)
        if not file_names:
            return
        base_names = [get_file_name_without_extension(file_name) for file_name in file_names]
        for upload_important_file in UPLOAD_REQUIRED_FILES:
            if upload_important_file not in base_names:
                return self.modal("warn", f"请包含{upload_important_file}文件")
        if UPLOAD_IMPORTANT_FILE in base_names:
            answer = self.modal("question", title=UPLOAD_IMPORTANT_FILE + "?", msg=f"你上传了{UPLOAD_IMPORTANT_FILE}, 确定要用吗, YES会覆盖现有的,NO会剔除这个文件,上传其他文件")
            if not answer:
                index = base_names.index(UPLOAD_IMPORTANT_FILE)
                base_names.pop(index)
                file_names.pop(index)

        colors = []
        important_file_names = []
        date_file_names = []
        for base_name, file_name in zip(base_names, file_names):
            if base_name == UPLOAD_IMPORTANT_FILE:
                colors.append(QColor(*COLOR_RED))
                important_file_names.append(file_name)
            elif base_name in UPLOAD_REQUIRED_FILES:
                colors.append(QColor(*COLOR_GREEN))
                important_file_names.append(file_name)
            else:
                colors.append(QColor(*COLOR_WHITE))
                date_file_names.append(file_name)
        fill_data(list_widget=self.file_date_value, items=base_names, colors=colors)

        # important_files = UPLOAD_REQUIRED_FILES + [UPLOAD_IMPORTANT_FILE]
        self.important_file_names = important_file_names
        self.date_file_names = date_file_names
        self.set_status_init()

    def download_file(self):
        """下载结果文件
        :return:
        """
        # 弹出一个文件保存对话框，获取用户选择的文件路径
        if not self.is_success:
            return self.modal("info", "请先执行或等待任务完成..." + self.status_text)
        file_path = self.download_file_modal(f"{TimeObj().time_str}_日报汇总.zip")
        if file_path:
            make_zip(DATA_TMP_PATH, file_path.rstrip(".zip"))
            # copy_file(DAILY_REPORT_RESULT_TEMPLATE_PATH, filePath)

    def do(self):
        """核心执行函数
        :return:
        """
        if self.is_running:
            return self.modal("warn", msg="程序执行中,请不要重新执行", done=True)
        elif not self.is_init or not self.date_file_names:
            return self.modal("warn", msg="请先上传文件", done=True)

        self.leader_word_value.clear()

        # 启动worker
        self.worker\
            .add_param("equal_buffer_value", self.equal_buffer_value.value())\
            .add_param("date_file_names", self.date_file_names)\
            .add_param("important_file_names", self.important_file_names)\
            .add_param("run_mute_checkbox", self.run_mute_checkbox.isChecked())\
            .start()

    def custom_set_random_leader_word(self, num_text, leader_word_variables):
        """设置领导的话
        :return:
        """
        self.num_text = num_text
        self.leader_word_variables = leader_word_variables
        self.clear_element("leader_word_value")
        before, after = get_txt_conf(LEADER_WORD_TEMPLATE_PATH, str).split("{motto}")
        motto = random.choice(get_txt_conf(MOTTO_TEXT_PATH, list))
        before_text = num_text + before.format(**leader_word_variables)
        after_text = after.format(**leader_word_variables)

        self.leader_word_value.append(before_text)
        self.leader_word_value.insertHtml(f'<font color="red">{motto}</font>')
        self.leader_word_value.insertHtml(f'<font color="black">{after_text}</font>')

    def reset(self):
        self.clear_element("leader_word_value")
        self.clear_element("file_date_value")
        self.set_status_empty()
        self.status_text = ""
        self.modal("info", title="Success", msg="重置成功")
