import os.path
import random

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QApplication

from lwx_project.client.const import UI_PATH
from lwx_project.scene.daily_report.const import *
from lwx_project.scene.daily_report.main import before_run, after_run
from lwx_project.scene.daily_report.steps import rename, calculate, sheet_picture
from lwx_project.utils.conf import get_txt_conf, set_txt_conf
from lwx_project.utils.file import get_file_name_without_extension, copy_file, make_zip
from lwx_project.utils.time_obj import TimeObj

UPLOAD_REQUIRED_FILES = ["代理期缴保费", "公司网点经营情况统计表", "农行渠道实时业绩报表"]  # 上传的文件必须要有
UPLOAD_IMPORTANT_FILE = "每日报表汇总"  # 如果有会放到tmp路径下


class MyDailyReportClient(QMainWindow):
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
    """
    def __init__(self):
        super(MyDailyReportClient, self).__init__()
        uic.loadUi(UI_PATH.format(file="daily_report.ui"), self)  # 加载.ui文件
        self.setWindowTitle("日报——By LWX")
        self.done = False

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
        self.new_file_name2date_dict = {}
        self.num_text = ""
        self.leader_word_variables = {}
        self.result_df_path = None
        self.do_button.clicked.connect(self.do)
        ## 2.3 随机生成名言警句按钮绑定
        self.motto_change_button.clicked.connect(self.motto_change)
        ## 2.4 拷贝按钮绑定
        self.copy_summary_button.clicked.connect(self.copy_leader_word)
        ## 2.5 下载文件按钮绑定
        self.download_file_button.clicked.connect(self.download_file)
        ## 2.6 高级配置：保存领导的话按钮
        self.save_leader_word_template_button.clicked.connect(
            lambda: self.save_config(LEADER_WORD_TEMPLATE_PATH, self.leader_word_template_value.toPlainText())
        )
        ## 2.7 高级配置：保存名言警句
        self.save_motto_list_button.clicked.connect(
            lambda: self.save_config(MOTTO_TEXT_PATH, self.motto_list_value.toPlainText())
        )

    def init_file_config(self):
        # 界面配置初始化
        self.leader_word_template_value.setText(get_txt_conf(LEADER_WORD_TEMPLATE_PATH, str))
        self.motto_list_value.setText(get_txt_conf(MOTTO_TEXT_PATH, str))

    def save_config(self, path, value):
        """保存配置
        :param path:
        :param value:
        :return:
        """
        set_txt_conf(path, value)
        QMessageBox.information(self, 'Success', '保存成功')

    def upload_file(self):
        """上传文件
        :return:
        """
        options = QFileDialog.Options()
        file_names, _ = QFileDialog.getOpenFileNames(self, "QFileDialog.getOpenFileName()", "", "Excel Files (*.xls*)", options=options)
        if not file_names:
            return
        base_names = [get_file_name_without_extension(file_name) for file_name in file_names]
        for upload_important_file in UPLOAD_REQUIRED_FILES:
            if upload_important_file not in base_names:
                QMessageBox.warning(self, "Warning", f"请包含{upload_important_file}文件")
                return
        for base_name in base_names:
            self.file_date_value.addItem(base_name)

        important_files = UPLOAD_REQUIRED_FILES + [UPLOAD_IMPORTANT_FILE]
        self.important_file_names = [file_name for file_name in file_names if get_file_name_without_extension(file_name) in important_files]
        self.date_file_names = [file_name for file_name in file_names if get_file_name_without_extension(file_name) not in important_files]

    def download_file(self):
        """下载结果文件
        :return:
        """
        # 弹出一个文件保存对话框，获取用户选择的文件路径
        if not os.path.exists(DAILY_REPORT_RESULT_TEMPLATE_PATH):
            QMessageBox.warning(self, "Warning", f"请先执行")
            return
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()", f"{TimeObj().time_str}_日报汇总.zip","All Files (*);;Text Files (*.zip)", options=options)
        if filePath:
            make_zip(DATA_TMP_PATH, filePath.rstrip(".zip"))
            # copy_file(DAILY_REPORT_RESULT_TEMPLATE_PATH, filePath)

    def do(self):
        """核心执行函数
        :return:
        """
        before_run()  # 清理路径
        self.leader_word_value.clear()

        # 第一步：重命名后显示修改的内容
        equal_buffer_value = self.equal_buffer_value.value()
        if not self.date_file_names:
            QMessageBox.warning(self, "Warning", f"请先上传文件")
            return
        if isinstance(equal_buffer_value, int) and equal_buffer_value >= 0:
            self.new_file_name2date_dict = rename.main(self.date_file_names, equal_buffer_value)
            # TODO: 这里的repaint不生效
            self.file_date_value.clear()
            for key, value in self.new_file_name2date_dict.items():
                self.file_date_value.addItem(f'{key}: {value}')
        # 第二步：执行宏
        result = calculate.main(
            copy2tmp_path_list=self.important_file_names,
            run_mute=self.run_mute_checkbox.isChecked()
        )
        """
        {
            "num_text": text,
            "leader_word_variables": leader_word_variables,
                motto=text_motto, season_char=today.season_in_char, month_num=today.month
            "result_df_path": DAILY_REPORT_TEMPLATE_PATH,
        }
        """
        self.num_text = result["num_text"]
        self.leader_word_variables = result["leader_word_variables"]
        self.set_random_leader_word()

        # 第三步截图
        for i in range(3, 14):  # 3,4,5...,13
            img_path = os.path.join(DATA_TMP_PATH, f"{i}.png")
            sheet_picture.main(
                excel_path=DAILY_REPORT_TMP_TEMPLATE_PATH,
                img_path=img_path,
                sheet_name_or_index=i,
                run_mute=self.run_mute_checkbox.isChecked()
            )
        self.done = True
        # 第三步：清理
        # after_run()

    def copy_leader_word(self):
        """拷贝领导的话
        :return:
        """
        text = self.leader_word_value.toPlainText()
        QApplication.clipboard().setText(text)

    def set_random_leader_word(self):
        """设置领导的话
        :return:
        """
        self.leader_word_value.clear()
        before, after = get_txt_conf(LEADER_WORD_TEMPLATE_PATH, str).split("{motto}")
        motto = random.choice(get_txt_conf(MOTTO_TEXT_PATH, list))
        before_text = self.num_text + before.format(**self.leader_word_variables)
        after_text = after.format(**self.leader_word_variables)

        self.leader_word_value.append(before_text)
        self.leader_word_value.insertHtml(f'<font color="red">{motto}</font>')
        self.leader_word_value.insertHtml(f'<font color="black">{after_text}</font>')

    def motto_change(self):
        """名言警句change
        :return:
        """
        if not self.done:
            QMessageBox.warning(self, "Warning", f"请先执行")
            return
        self.set_random_leader_word()
