import typing

from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QListWidgetItem, QHBoxLayout, QPushButton, QListWidget, QMenu, QAction


class ListWidgetWrapper:
    def __init__(self, list_widget, add_rows_button=False, del_rows_button=False, double_clicked=None):
        self.list_widget = list_widget
        new_list = self.__add_buttons(add_rows_button, del_rows_button)
        if new_list is not None:
            self.list_widget = new_list

        if double_clicked:
            self.list_widget.itemDoubleClicked.connect(double_clicked)

    def __add_buttons(self, add_rows_button, del_rows_button):
        if not add_rows_button and not del_rows_button:
            return

        # 获取list所在的布局
        layout = self.list_widget.parent().layout()

        # 获取list在布局中的位置
        index = layout.indexOf(self.list_widget)

        # 创建一个水平布局，并添加两个按钮
        hbox = QHBoxLayout()

        # 创建两个按钮
        if add_rows_button:
            add_item_button = QPushButton('末尾添加一项', self.list_widget.parent())
            add_item_button.clicked.connect(self.__add_item)
            hbox.addWidget(add_item_button)
        if del_rows_button:
            del_item_button = QPushButton('删除选中项', self.list_widget.parent())
            del_item_button.clicked.connect(self.__delete_item)
            hbox.addWidget(del_item_button)

        # 创建一个新的list，并复制原来list的所有内容
        new_list = QListWidget(self.list_widget.parent())
        for i in range(self.list_widget.count()):
            new_list.addItem(self.list_widget.item(i).text())

        # 删除原来的list
        layout.removeWidget(self.list_widget)
        self.list_widget.setParent(None)

        # 在原来list的位置添加新的组合
        layout.insertLayout(index, hbox)
        layout.insertWidget(index + 1, new_list)
        return new_list

    def __add_item(self):
        # 在list的末尾添加一个新的项
        item_obj = QListWidgetItem('NEW')
        item_obj.setFlags(item_obj.flags() | Qt.ItemIsEditable)
        self.list_widget.addItem(item_obj)

    def __delete_item(self):
        # 删除list中选中的项
        for item in self.list_widget.selectedItems():
            self.list_widget.takeItem(self.list_widget.row(item))

    def add_item(self, item, color=None, editable=False):
        item_obj = QListWidgetItem(item)

        # 设置项的flags属性为Qt.ItemIsEditable
        if editable:
            item_obj.setFlags(item_obj.flags() | Qt.ItemIsEditable)

        if color:
            item_obj.setBackground(QColor(*color))
        self.list_widget.addItem(item_obj)

    def fill_data_with_color(self, items, colors=None, editable=False):
        """以背景颜色填充list容器
        :param items:
        :param colors:
        :param editable:
        :return:
        """
        colors = colors or [None] * len(items)
        for item, color in zip(items, colors):
            self.add_item(item, color=color, editable=editable)

    def get_data_as_list(self) -> list:
        return [self.list_widget.item(i).text() for i in range(self.list_widget.count())]

    def get_data_as_str(self, join="\n") -> str:
        return join.join([self.list_widget.item(i).text() for i in range(self.list_widget.count())])

    def get_text_by_index(self, index):
        if self.list_widget.count() == 0:
            return None
        if index < 0:
            index = self.list_widget.count() + index
        if index >= self.list_widget.count():
            return None
        item = self.list_widget.item(index)
        original_text = item.text()
        return original_text

    def set_text_by_index(self, index, text, color=None):
        if self.list_widget.count() == 0:
            return None
        if index < 0:
            index = self.list_widget.count() + index
        if index >= self.list_widget.count():
            return None
        item = self.list_widget.item(index)
        item.setText(text)
        if color is not None:
            item.setBackground(QColor(*color))
        return None

    def remove_item_by_index(self, index):
        if self.list_widget.count() == 0:
            return None
        if index < 0:
            index = self.list_widget.count() + index
        if index >= self.list_widget.count():
            return None
        # 移除并自动析构 item
        self.list_widget.takeItem(index)
        return None


    def get_index_by_text(self, text):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            original_text = item.text()
            if original_text == text:
                return i
        return None

    def get_selected_text(self):
        selected_items = self.list_widget.selectedItems()
        selected_texts = [item.text() for item in selected_items]
        return selected_texts

    def bind_double_click_func(self, on_double_click: typing.Callable[[int, str], None]):
        # 定义一个槽函数，接收 QListWidgetItem 并调用用户传入的 func
        def on_double_click_wrapper(item: QListWidgetItem):  # 默认的是传 QListWidgetItem 对象
            index = self.list_widget.row(item)
            on_double_click(index, item.text())  # 如何获取索引

        # 断开可能已存在的连接（避免重复绑定）
        try:
            self.list_widget.itemDoubleClicked.disconnect()
        except TypeError:
            # 如果没有连接过，disconnect 会抛出 TypeError，忽略即可
            pass

        # 绑定双击信号
        self.list_widget.itemDoubleClicked.connect(on_double_click_wrapper)
        return self

    def bind_right_click_menu(
            self,
            on_right_click: typing.Dict[str, typing.Callable[[int, str], None]]
    ):
        """
        on_right_click 是一个 dict:
            key: 菜单项显示的文字（str）
            value: 回调函数，签名 func(index: int, text: str) -> None
        """
        # 启用自定义上下文菜单
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)

        # 定义菜单显示槽函数
        def show_context_menu(pos: QPoint):
            # 获取全局坐标
            global_pos = self.list_widget.mapToGlobal(pos)

            # 判断点击位置是否有 item
            item = self.list_widget.itemAt(pos)
            if item is None:
                return  # 点击空白处不显示菜单

            index = self.list_widget.row(item)
            text = item.text()

            # 创建菜单
            menu = QMenu(self.list_widget)
            for label, callback in on_right_click.items():
                action = QAction(label, menu)
                # 使用闭包捕获当前的 index 和 text（注意避免循环变量陷阱）
                action.triggered.connect(
                    lambda checked, idx=index, txt=text, cb=callback: cb(idx, txt)
                )
                menu.addAction(action)

            # 显示菜单
            menu.exec_(global_pos)

        # 断开旧连接（避免重复绑定）
        try:
            self.list_widget.customContextMenuRequested.disconnect()
        except TypeError:
            pass  # 未连接过，忽略

        # 绑定新连接
        self.list_widget.customContextMenuRequested.connect(show_context_menu)
        return self

    def clear(self):
        self.list_widget.clear()


# todo: 优化这里的方法
def fill_data(list_widget, items, colors):
    """以背景颜色填充list容器
    :param list_widget:
    :param items:
    :param colors:
    :return:
    """
    for item, color in zip(items, colors):
        item_obj = QListWidgetItem(item)
        item_obj.setBackground(QColor(color))
        list_widget.addItem(item_obj)
