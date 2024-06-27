import json
import traceback

from PyQt5.QtCore import pyqtSignal, QThread, QTimer, QTime
from PyQt5.QtWidgets import QWidget, QLabel, QMainWindow, QMessageBox, QListWidget, QFileDialog, QApplication
from PyQt5.QtGui import QPixmap

from lwx_project.client.const import *
from lwx_project.client.utils.exception import ClientWorkerException
from lwx_project.client.utils.message_widget import TipWidgetWithCountDown
from lwx_project.utils.logger import logger_sys_error


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
    def modal(self, level, msg, title=None, done=None, **kwargs):
        """
        :param level:
        :param msg:
        :param title:
        :param done:
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
            TipWidgetWithCountDown(msg=msg, count_down=count_down)

    # 上传
    def upload_file_modal(self, patterns, multi=False):
        """
        :param patterns:
            [(pattern_name, pattern), (pattern_name, pattern)]  ("Excel Files", "*.xls*")
        :param multi: 是否支持多选
        :return:
        """
        if len(patterns) == 2 and isinstance(patterns[0], str):
            patterns = [patterns]
        options = QFileDialog.Options()
        pattern_str = ";;".join([f"{pattern_name} ({pattern})" for pattern_name, pattern in patterns])
        func = QFileDialog.getOpenFileNames if multi else QFileDialog.getOpenFileName
        file_name_or_list, _ = func(self, "QFileDialog.getOpenFileName()", "", pattern_str, options=options)
        return file_name_or_list

    # 下载
    def download_file_modal(self, default_name: str):
        options = QFileDialog.Options()
        suffix = default_name.split(".")[-1]
        file_path, _ = QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", default_name,
                                                   f"All Files (*);;Text Files (*.{suffix})", options=options)
        return file_path

    # 复制
    @staticmethod
    def copy2clipboard(text: str):
        QApplication.clipboard().setText(text)

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
