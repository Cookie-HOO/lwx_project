from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QListWidgetItem, QHBoxLayout, QPushButton, QListWidget


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

    def fill_data_with_color(self, items, colors=None, editable=False):
        """以背景颜色填充list容器
        :param items:
        :param colors:
        :param editable:
        :return:
        """
        colors = colors or [None] * len(items)
        for item, color in zip(items, colors):
            item_obj = QListWidgetItem(item)

            # 设置项的flags属性为Qt.ItemIsEditable
            if editable:
                item_obj.setFlags(item_obj.flags() | Qt.ItemIsEditable)

            if color:
                item_obj.setBackground(QColor(*color))
            self.list_widget.addItem(item_obj)

    def get_data_as_list(self) -> list:
        return [self.list_widget.item(i).text() for i in range(self.list_widget.count())]

    def get_data_as_str(self, join="\n") -> str:
        return join.join([self.list_widget.item(i).text() for i in range(self.list_widget.count())])

    def get_text_by_index(self, index):
        if index < 0:
            index = self.list_widget.count() + index
        if index >= self.list_widget.count():
            return None
        item = self.list_widget.item(index)
        original_text = item.text()
        return original_text

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

    def set_text_by_index(self, index, text, color=None):
        item = self.list_widget.item(index)
        item.setText(text)
        if color is not None:
            item.setBackground(QColor(*color))

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
