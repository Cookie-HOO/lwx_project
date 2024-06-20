from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QListWidgetItem


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
