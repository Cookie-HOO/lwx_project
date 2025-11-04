import os
import time
import typing

from PyQt5.QtGui import QMovie, QIcon, QColor, QImage, QPixmap
from PyQt5.QtWidgets import QMessageBox, QWidget, QLabel, QVBoxLayout, QTextBrowser, QDialog, QSizePolicy, QPushButton, \
    QHBoxLayout
from PyQt5.QtCore import QTimer, QTime, Qt

from lwx_project.const import STATIC_PATH


class TipWidgetWithCountDown(QMessageBox):
    """自定义的一个倒计时自动关闭的MessageBox"""
    def __init__(self, msg, count_down):
        super().__init__()
        self.time_left = count_down
        self.msg = msg
        self.initUI()
        self.exec_()

    def initUI(self):
        self.setWindowTitle(f'{self.time_left}秒后自动关闭')
        # self.setGeometry(300, 300, 250, 150)
        self.setIcon(QMessageBox.Information)
        self.setText(self.msg)
        self.setStandardButtons(QMessageBox.Ok)
        self.setDefaultButton(QMessageBox.Ok)
        # self.show()

        # 创建一个定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_title)
        self.timer.start(1000)  # 每秒触发一次

    def update_title(self):
        self.time_left -= 1
        self.setWindowTitle(f'{self.time_left}秒后自动关闭')
        if self.time_left == 0:
            self.timer.stop()
            self.close()


class CustomMessageBox(QMessageBox):
    def __init__(self, title, msg, width, height, funcs, parent=None):
        super().__init__(parent)
        self.title = title
        self.msg = msg
        self.width = width
        self.height = height

        self.setWindowTitle(title)
        # self.setText(msg)

        if funcs:
            for func_item in funcs:
                text = func_item.get("text")
                func = func_item.get("func")
                # QMessageBox.ActionRole | QMessageBox.AcceptRole | QMessageBox.RejectRole
                # QMessageBox.DestructiveRole | QMessageBox.HelpRole | QMessageBox.YesRole | QMessageBox.NoRole
                # QMessageBox.ResetRole | QMessageBox.ApplyRole
                role = func_item.get("role")
                color = func_item.get("color")
                bg_color = func_item.get("bg_color")
                icon = func_item.get("icon")  # icon的绝对路径
                type_ = func_item.get("type_")  # icon的绝对路径
                if role:
                    custom_button = self.addButton(text, role)
                    if func:
                        custom_button.clicked.connect(func)
                    if color:
                        custom_button.setStyleSheet(f'QPushButton {{ color: {color.name()}; }}')
                    if bg_color:
                        custom_button.setStyleSheet(f'QPushButton {{ background-color: {bg_color.name()}; }}')
                    if icon:
                        custom_button.setIcon(QIcon(icon))

        self.setStandardButtons(QMessageBox.Ok)
        # self.setStandardButtons(QMessageBox.Ok | QMessageBox.Open | QMessageBox.Save |
        #                            QMessageBox.Cancel | QMessageBox.Close | QMessageBox.Discard |
        #                            QMessageBox.Apply | QMessageBox.Reset | QMessageBox.RestoreDefaults |
        #                            QMessageBox.Help | QMessageBox.SaveAll | QMessageBox.Yes |
        #                            QMessageBox.YesToAll | QMessageBox.No | QMessageBox.NoToAll |
        #                            QMessageBox.Abort | QMessageBox.Retry | QMessageBox.Ignore)
        # 设置自定义布局
        if "html" in self.msg:
            self.setupCustomLayout()
        else:
            self.setText(self.msg)

    def setupCustomLayout(self):
        # 获取消息框的布局
        layout = self.layout()

        # 创建一个自定义的widget和layout来控制大小
        custom_widget = QWidget()
        custom_layout = QVBoxLayout(custom_widget)

        # 添加一个自定义的label（可以添加更多的widgets）
        text_widget = QTextBrowser()
        text_widget.setHtml(self.msg)
        # label = QLabel(self.msg)
        custom_layout.addWidget(text_widget)

        # 将自定义的widget添加到消息框的布局中
        layout.addWidget(custom_widget, 0, 0)

        # 设置自定义widget的最小大小
        if self.width and self.height:
            custom_widget.setMinimumSize(self.width, self.height)


class MyQMessageBox(QWidget):
    """支持html作为msg，且支持width和height"""
    def __init__(self, title, msg, width=None, height=None, funcs=None):
        """
        funcs: [{"func": func, "text": "", "role"}]
        """
        super().__init__()
        self.title = title
        self.msg = msg
        self.width = width
        self.height = height
        self.funcs = funcs
        self.initUI()

    def initUI(self):
        # 创建并显示自定义的消息框
        msgBox = CustomMessageBox(self.title, self.msg, self.width, self.height, self.funcs)

        retval = msgBox.exec_()
        # print("返回值:", retval)


class TipWidgetWithLoading(QDialog):
    """
    tip_with_loading = TipWidgetWithLoading(title="加载中...")
    tip_with_loading.show()
    tip_with_loading.hide()
    """

    def __init__(self, titles=None):
        super().__init__()
        self.setWindowTitle("加载中...")
        self.titles = titles or []  # 多个title轮播
        self.titles_pointer = 0

        self.label = QLabel(self)
        self.label.setStyleSheet("background-color: transparent;")  # todo: 如何透明
        self.title_label = QLabel("", self)
        self.title_label.setAlignment(Qt.AlignCenter)  # 让文本居中对齐

        self.time_label = QLabel(self)
        self.time_label.setAlignment(Qt.AlignCenter)  # 让文本居中对齐

        self.movie = QMovie(os.path.join(STATIC_PATH, "loading_lwx.gif"))  # 你的GIF文件路径
        self.label.setMovie(self.movie)
        self.label.setScaledContents(True)

        self.cost_timer = QTimer(self)
        self.cost_timer.timeout.connect(self.update_cost)

        self.title_timer = QTimer(self)
        self.title_timer.timeout.connect(self.update_title)

        self.start_time = QTime()

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(self.title_label)
        layout.addWidget(self.label)
        layout.addWidget(self.time_label)

        self.setLayout(layout)

    def showEvent(self, event):
        self.titles_pointer = 0
        self.movie.start()
        self.start_time.start()
        self.cost_timer.start(10)

        if self.titles:
            self.title_timer.start(500)
        # QTimer.singleShot(100, self.start_loading)

    def hideEvent(self, event):
        self.movie.stop()
        self.cost_timer.stop()

        self.titles_pointer = 0
        self.titles = []

    # def start_loading(self):
    #     self.titles_pointer = 0
    #     self.movie.start()
    #     self.start_time.start()
    #     self.cost_timer.start(10)
    #
    #     if self.titles:
    #         self.title_timer.start(500)

    def update_cost(self):
        elapsed = self.start_time.elapsed() / 1000.0
        self.time_label.setText("耗时：{:.2f}秒".format(elapsed))

    def update_title(self):
        if self.titles:
            title_index = self.titles_pointer % len(self.titles)
            title = self.titles[title_index]
            self.title_label.setText(title)
            self.setWindowTitle(title)
            self.titles_pointer += 1

    def set_titles(self, titles):
        self.titles = titles
        return self


import typing
import os
from PyQt5.QtWidgets import (
    QDialog, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt


class TipWidgetWithImgGallery(QDialog):
    """展示一个modal，可以上下（左右）切换当前图片
    1. 接收图片的bytes的list
    2. 点击左右可以切换
    3. 展示总共几个，当前是第几个
    4. 可选：每张图下方显示对应的文字说明（caption）
    """

    def __init__(
        self,
        imgs: typing.List[bytes] = None,
        imgs_path: typing.List[str] = None,
        captions: typing.List[str] = None,
        width=None,
        height=None
    ):
        super().__init__()
        imgs = imgs or []
        if not imgs:
            if not imgs_path:
                raise ValueError("必须提供 imgs 或 imgs_path")
            for img_path in imgs_path:
                if not os.path.exists(img_path):
                    raise FileNotFoundError(img_path)
                with open(img_path, "rb") as f:
                    imgs.append(f.read())

        self.imgs = imgs
        self.total = len(imgs)
        if self.total == 0:
            raise ValueError("imgs 不能为空")

        # 处理 captions
        if captions is not None:
            if len(captions) != self.total:
                raise ValueError("captions 长度必须与图片数量一致")
            self.captions = captions
        else:
            self.captions = [""] * self.total  # 默认为空字符串

        self.current_index = 0

        self.setWindowTitle("图片预览")
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | Qt.WindowCloseButtonHint)

        # 图片显示区域
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setMinimumSize(width or 600, height or 800)

        # 文字说明（caption）
        self.caption_label = QLabel()
        self.caption_label.setAlignment(Qt.AlignCenter)
        self.caption_label.setWordWrap(True)
        self.caption_label.setStyleSheet("font-size: 14px; color: gray; padding: 8px;")

        # 底部信息：当前/总数
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignCenter)

        # 按钮
        self.prev_button = QPushButton("◀ 上一张")
        self.next_button = QPushButton("下一张 ▶")

        self.prev_button.clicked.connect(self.show_prev)
        self.next_button.clicked.connect(self.show_next)

        # 布局
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.next_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.image_label)
        main_layout.addWidget(self.caption_label)  # 新增：文字说明
        main_layout.addWidget(self.info_label)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        # 初始显示第一张
        self.update_display()

    def update_display(self):
        """根据 current_index 更新图片、文字和信息"""
        img_bytes = self.imgs[self.current_index]
        qimg = QImage.fromData(img_bytes)
        if qimg.isNull():
            self.image_label.setText("无法加载图片")
            self.caption_label.setText("")
        else:
            pixmap = QPixmap.fromImage(qimg)
            self.image_label.setPixmap(pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))
            self.caption_label.setText(self.captions[self.current_index])

        self.info_label.setText(f"{self.current_index + 1} / {self.total}")

        # 更新按钮状态
        self.prev_button.setEnabled(self.current_index > 0)
        self.next_button.setEnabled(self.current_index < self.total - 1)

    def show_prev(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.update_display()

    def show_next(self):
        if self.current_index < self.total - 1:
            self.current_index += 1
            self.update_display()

    def keyPressEvent(self, event):
        """支持键盘左右键切换"""
        if event.key() == Qt.Key_Left:
            self.show_prev()
        elif event.key() == Qt.Key_Right:
            self.show_next()
        elif event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        """窗口大小变化时重新缩放图片"""
        if self.imgs:
            self.update_display()
        super().resizeEvent(event)

    def show_gallery(self):
        """方便调用的接口，类似 exec_()"""
        return self.exec_()

# 测试代码
# from PyQt5.QtWidgets import QApplication, QDialog, QLabel, QVBoxLayout
# from PyQt5.QtGui import QMovie
# from PyQt5.QtCore import QTimer, QTime, Qt
# import sys
# app = QApplication(sys.argv)
# dialog = TipWidgetWithLoading()
# dialog.show()
# # dialog.hide()
# sys.exit(app.exec_())