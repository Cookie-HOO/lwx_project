import json
import shutil
import traceback
import typing

import pandas as pd
from PyQt5.QtCore import pyqtSignal, QThread, QTimer, QTime
from PyQt5.QtWidgets import QWidget, QLabel, QMainWindow, QMessageBox, QListWidget, QFileDialog, QApplication, QPushButton
from PyQt5.QtGui import QPixmap

from lwx_project.client.const import *
from lwx_project.client.utils.exception import ClientWorkerException
from lwx_project.client.utils.message_widget import TipWidgetWithCountDown
from lwx_project.utils.file import get_file_name_without_extension, copy_file, get_file_name_with_extension, make_zip
from lwx_project.utils.logger import logger_sys_error
from lwx_project.utils.time_obj import TimeObj


class Background(QWidget):
    def __init__(self, parent=None):
        super(Background, self).__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setGeometry(100, 100, 500, 500)
        self.setWindowTitle('Background Demo')

        # 设置背景图片
        self.background = QLabel(self)
        self.background.setPixmap(QPixmap(STATIC_FILE_PATH.format(file="background1.jpg")))
        self.background.setGeometry(0, 0, 500, 500)


class BaseWorker(QThread):
    # 生命周期信号
    after_start_signal = pyqtSignal()
    refresh_signal = pyqtSignal(str)  # refresh的文本,可以显示在状态栏中
    before_finished_signal = pyqtSignal()
    # 元素操作信号
    modal_signal = pyqtSignal(str, str)  # info|warn|error, msg  其中error会终止程序
    clear_element_signal = pyqtSignal(str)  # clear
    append_element_signal = pyqtSignal(str, str)  # add
    set_element_signal = pyqtSignal(str, str)  # clear + add、

    # 链式添加参数
    def add_param(self, param_key, param_value):
        setattr(self, param_key, param_value)
        return self

    def add_params(self, param_dict):
        for param_key, param_value in param_dict.items():
            setattr(self, param_key, param_value)
        return self

    # 获取参数
    def get_param(self, key):
        return getattr(self, key)

    # run的wrapper: 开始和结束报错的生命周期
    def run(self):
        self.after_start_signal.emit()
        try:
            self.my_run()
        except ClientWorkerException as e:
            return self.modal_signal.emit("error", str(e))
        except Exception as e:
            return self.modal_signal.emit("error", traceback.format_exc())
        self.before_finished_signal.emit()

    @logger_sys_error
    def my_run(self):
        raise NotImplementedError


class BaseWindow(QMainWindow):
    def __init__(self):
        super(BaseWindow, self).__init__()
        self.modal_list = []

    # 初始化场景说明按钮
    # 每个子场景有自己的UI，无法在继承父类时自动执行，需子场景手动调用
    def init_help_button(self, show_text, pos=None, button_text="❓"):
        default_text = """
=========== 图示 ===========
第一个图标表示是否必须
    ❗表示必须（校验不过无法执行此场景）
    ❓表示非必须（但是如果提供了格式校验不通过一样无法执行）
第二个图标表示：内容从哪里来
    ⛔表示由系统生成，不要修改
    🔧表示在场景的高级设置中可以修改
    📗表示可上传的同名文件，会被覆盖（覆盖时会有提示）
    🪟表示在操作界面，由用户操作产生
注：
    1. 如果Important文件不合规，点击上传文件会有报错提示（无法上传文件）
    2. 如果上传的文件不合规，会有报错提示（无法执行场景）
"""
        help_button = QPushButton(button_text, self)
        # 设置按钮的位置和大小
        pos = pos or (150, 0, 50, 25)
        help_button.setGeometry(*pos)  # pos： 150, 0, 20, 20
        # 连接按钮的点击事件到showDoc方法

        # help_button.clicked.connect(lambda:
        #                             self.modal("info", title="Documentation", msg=default_text + show_text))
        help_button.clicked.connect(lambda: (
            self.modal("info", title="Documentation", msg=show_text, async_run=True, count_down=60),
            self.modal("info", title="Legend", msg=default_text, async_run=True, count_down=5),
        ))

    ############  元素操作: 直接调用, 或者是worker发送事件的消费者 ############
    # 清除元素
    def clear_element(self, element):
        ele = getattr(self, element)
        if ele is None:
            return self.modal("warn", f"no such element: {element}")
        ele.clear()

    # 元素追加内容
    def append_element(self, element, item):
        pass

    # 元素覆盖内容
    def set_element(self, element, item):
        self.clear_element(element)
        ele = getattr(self, element)
        if ele is None:
            self.modal("warn", f"no such element: {element}")
            return
        if isinstance(ele, QListWidget):
            ele.addItems(json.loads(item))

    ############ 组件封装 ############
    def modal(self, level, msg, title=None, done=None, async_run=None, **kwargs):
        """
        :param level:
        :param msg:
        :param title:
        :param done:
        :param async_run: 是否异步执行，即弹窗之后不影响UI继续进行
            默认False，即弹窗之后必须等待用户手动ok或手动关闭
            仅支持tip（默认True）info（默认False）
        :param kwargs
            count_down
        :return:
        """
        title = title or level
        if level == "error" and done is None:
            done = True

        if level == "info":
            if done:
                self.done = True
            if async_run:  # 只有info支持 async_run
                msgBox = QMessageBox(QMessageBox.Information, title, msg)
                msgBox.finished.connect(lambda: self.modal_list.remove(msgBox))  # 在弹窗关闭时从列表中移除
                msgBox.show()
                self.modal_list.append(msgBox)  # 将弹窗添加到列表中，保持引用
            else:
                QMessageBox.information(self, title, msg)
        elif level == "warn":
            if done:
                self.done = True
            QMessageBox.warning(self, title, msg)
        elif level == "error":
            if done:
                self.set_status_failed()
                self.done = True
            QMessageBox.critical(self, title, msg)
        elif level == "check_yes":  # 只要yes（点击No或者关闭，reply都是一个值）
            reply = QMessageBox.question(
                self, title, msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            return reply == QMessageBox.Yes
        elif level == "tip":
            count_down = kwargs.get("count_down", 3)
            async_run = async_run or async_run is None  # 默认就是异步
            TipWidgetWithCountDown(msg=msg, count_down=count_down, async_run=async_run, outer_container=self.modal_list)

    # 上传
    def upload_file_modal(
            self, patterns=("Excel Files", "*.xlsx"), multi=False,
            required_base_name_list=None, copy_to: str = None,
            optional_base_name_list=None,
            overwritten_base_name_list=None, overwritten_to: str = None
    ) -> typing.Union[str, list, None]:
        """
        :param patterns:
            [(pattern_name, pattern), (pattern_name, pattern)]  ("Excel Files", "*.xls*")
        :param multi: 是否支持多选
        :param required_base_name_list: 上传的文件必須有的文件名,，注意这个参数的元素不含后缀且没有路径，只有文件名
        :param optional_base_name_list: 上传的文件可以有的文件名,，注意这个参数的元素不含后缀且没有路径，只有文件名，如果指定了，会影响返回文件的顺序
        :param copy_to: 如果制定了这个参数，会将上传的文件一并拷贝到这个路径
        :param overwritten_base_name_list: 如果制定了这个参数，上传的文件中如果出现此文件会警告，要将这个文件覆盖到important文件中吗
        :param overwritten_to: important的路径
        :return:
        """
        if len(patterns) == 2 and isinstance(patterns[0], str):
            patterns = [patterns]
        options = QFileDialog.Options()
        pattern_str = ";;".join([f"{pattern_name} ({pattern})" for pattern_name, pattern in patterns])
        func = QFileDialog.getOpenFileNames if multi else QFileDialog.getOpenFileName
        file_name_or_list, _ = func(self, "QFileDialog.getOpenFileName()", "", pattern_str, options=options)
        if not file_name_or_list:
            return None
        # 处理必须要包含某些required_base_name的情况
        required_list = required_base_name_list or []
        file_name_list = file_name_or_list if isinstance(file_name_or_list, list) else [file_name_or_list]
        file_name_base_names = [get_file_name_without_extension(file_name) for file_name in file_name_list]
        order_index_list = []
        for required in required_list:
            if required not in file_name_base_names:
                self.modal("warn", f"请包含{required}文件")
                return []
            else:
                order_index_list.append(file_name_base_names.index(required))

        # 处理option文件的情况
        optional_list = optional_base_name_list or []
        for optional in optional_list:
            if optional in file_name_base_names:
                order_index_list.append(file_name_base_names.index(optional))

        # 处理可能的文件覆盖的情况
        for overwritten in overwritten_base_name_list or []:
            if overwritten in file_name_base_names:
                overwritten_index = file_name_base_names.index(overwritten)
                overwritten_path = file_name_list[overwritten_index]
                answer = self.modal(
                    "check_yes", title=overwritten + "?",
                    msg=f"你上传了{overwritten}, 确定要用吗, YES会覆盖现有的,NO会剔除这个文件,上传其他文件"
                )
                if answer:
                    copy_file(overwritten_path, overwritten_to)

        # 如果指定了路径，将所有文件拷贝过去
        if copy_to:
            for file_name in file_name_list:
                new_path = os.path.join(copy_to, get_file_name_with_extension(file_name))
                copy_file(file_name, new_path)

        # 按照必要性的顺序排序
        new_list = [file_name_or_list[ind] for ind in order_index_list]
        remain_list = [v for v in file_name_or_list if v not in new_list]
        new_list.extend(remain_list)
        return new_list

    # 下载
    def download_file_modal(self, default_name: str):
        options = QFileDialog.Options()
        suffix = default_name.split(".")[-1]
        file_path, _ = QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", default_name,
                                                   f"All Files (*);;Text Files (*.{suffix})", options=options)
        return file_path

    def download_zip_or_file_from_path(self, path_or_df, default_topic):
        if isinstance(path_or_df, str):
            path = path_or_df
            if len(os.listdir(path)) > 1:
                file_path = self.download_file_modal(f"{TimeObj().time_str}_{default_topic}.zip")
                if not file_path:
                    return
                make_zip(path, file_path.rstrip(".zip"))
            else:
                file_path = self.download_file_modal(f"{TimeObj().time_str}_{os.listdir(path)[0]}")
                if not file_path:
                    return
                copy_file(os.path.join(path, os.listdir(path)[0]), file_path)
        elif isinstance(path_or_df, pd.DataFrame):
            df = path_or_df
            file_path = self.download_file_modal(f"{TimeObj().time_str}_{default_topic}.csv")
            if not file_path:
                return
            df.to_csv(file_path, index=False)

    # 复制
    @staticmethod
    def copy2clipboard(text: str):
        QApplication.clipboard().setText(text)

    @staticmethod
    def clear_tmp_and_copy_important(tmp_path=None, important_path=None):
        # 1. 创建路径
        shutil.rmtree(tmp_path, ignore_errors=True)
        os.makedirs(tmp_path, exist_ok=True)
        if important_path:
            # 2. 拷贝关键文件到tmp路径
            for file in os.listdir(important_path):
                if not file.startswith("~") and (file.endswith("xlsx") or file.endswith("xlsm")):
                    old_path = os.path.join(important_path, file)
                    new_path = os.path.join(tmp_path, file)
                    copy_file(old_path, new_path)

    ############ wrapper类函数: 函数式编程思想,减少代码 ############
    def func_modal_wrapper(self, msg, func, *args, **kwargs):
        func(*args, **kwargs)
        self.modal("info", msg)

    def modal_func_wrapper(self, limit, warn_msg, func, *args, **kwargs):
        if not limit:
            return self.modal("warn", warn_msg)
        func(*args, **kwargs)


class WindowWithMainWorker(BaseWindow):
    """主窗口的一种模式
    在这个窗口中,存在一个主任务,窗口的设计都围绕这个主任务进行
    """
    SIGNAL_SUFFIX = "_signal"

    def __init__(self):
        super(WindowWithMainWorker, self).__init__()
        # 将worker的signal自动注册上handler
        self.worker = self.register_worker()
        for worker_signal in self.worker.__dir__():
            if worker_signal.endswith(self.SIGNAL_SUFFIX):
                worker_handler = worker_signal[:-len(self.SIGNAL_SUFFIX)]
                worker_signal = getattr(self.worker, worker_signal)
                worker_signal.connect(getattr(self, worker_handler))
        # 计时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.start_time = None
        # 任务状态与显示
        self.refresh_text = ""  # worker中发出来后,绑定到这个变量,被statusbar更新
        self.status_text = ""  # 完整状态信息,有运行时间 + refresh_text
        self.__status = None

    # 注册一个Worker
    def register_worker(self) -> BaseWorker:
        pass

    ############  生命周期状态 ############
    @property
    def is_empty_status(self):
        return self.__status is None  # 原始状态

    @property
    def is_init(self):
        return self.__status == "init"

    @property
    def is_running(self):
        return self.__status == "running"

    @property
    def is_done(self):
        return self.__status in ["success", "failed"]

    @property
    def is_success(self):
        return self.__status == "success"

    @property
    def is_failed(self):
        return self.__status == "failed"

    def set_status_empty(self):
        self.timer.stop()
        self.__status = None

    def set_status_init(self):
        self.__status = "init"

    def set_status_running(self):
        self.__status = "running"

    def set_status_success(self):
        elapsed_time = self.start_time.secsTo(QTime.currentTime())
        self.statusBar.showMessage(f"Success: Last for: {elapsed_time} seconds")
        self.timer.stop()
        self.__status = "success"
        self.modal("info", title="Finished", msg=f"执行完成,共用时{self.start_time.secsTo(QTime.currentTime())}秒")

    def set_status_failed(self):
        elapsed_time = self.start_time.secsTo(QTime.currentTime())
        self.statusBar.showMessage(f"Failed: Last for: {elapsed_time} seconds")
        self.timer.stop()
        self.__status = "failed"

    ############  生命周期: 直接调用, 或者是worker发送事件的消费者 ############
    # 生命周期: worker任务启动
    def after_start(self):
        self.set_status_running()
        self.start_time = QTime.currentTime()
        self.timer.start(1000)  # 更新频率为1秒

    # 生命周期: worker停止前每秒刷新的内容
    def update_time(self):  # 计时器停止,自然就没人调用了,不用判断状态
        elapsed_time = self.start_time.secsTo(QTime.currentTime())
        self.status_text = f"Last for: {elapsed_time} seconds :: {self.refresh_text}"
        self.statusBar.showMessage(self.status_text)

    def refresh(self, refresh_text):
        self.refresh_text = refresh_text

    # 生命周期: worker停止前
    def before_finished(self):
        self.set_status_success()

    # 工具函数
    def download_zip_or_file_from_path(self, path_or_df, default_topic, exclude=None):
        """下载结果文件
        :return:
        """
        # 弹出一个文件保存对话框，获取用户选择的文件路径
        if not self.is_success:
            return self.modal("info", "请先执行或等待任务完成..." + self.status_text)
        super().download_zip_or_file_from_path(path_or_df, default_topic)
