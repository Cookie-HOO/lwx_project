import pandas as pd
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QTableWidgetItem

"""
pyqt5的table组件，的set和get 
"""


def fill_data(table_widget, df, style_func=None):
    """
    :param table_widget:
    :param df:
    :param style_func:
        def style_func(df, i, j):  # df, i行 j列
            return QColor(r,g,b)
    :return:
    """
    cols_to_drop = [i for i in df.columns if i.startswith('__')]
    # df删除 no_use_cols 列
    fill_df = df.drop(cols_to_drop, axis=1)
    # 将dataframe的数据写入QTableWidget
    table_widget.setRowCount(fill_df.shape[0])
    table_widget.setColumnCount(fill_df.shape[1])
    table_widget.setHorizontalHeaderLabels(fill_df.columns)
    for i in range(fill_df.shape[0]):
        for j in range(fill_df.shape[1]):
            item = QTableWidgetItem(str(fill_df.iloc[i, j]))
            if style_func:
                item.setBackground(QBrush(style_func(fill_df, i, j)))  # 设置背景颜色为红色
            table_widget.setItem(i, j, item)


def get_data(table_widget):
    headers = []
    for i in range(table_widget.columnCount()):
        header = table_widget.horizontalHeaderItem(i)
        if header is not None:
            headers.append(header.text())
        else:
            headers.append(f'Column{i}')
    data = []
    for i in range(table_widget.rowCount()):
        row_data = []
        for j in range(table_widget.columnCount()):
            item = table_widget.item(i, j)
            if item is not None:
                row_data.append(item.text())
            else:
                row_data.append('')
        data.append(row_data)
    df = pd.DataFrame(data, columns=headers)
    return df
