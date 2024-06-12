import pandas as pd
from PyQt5.QtWidgets import QTableWidgetItem

"""
pyqt5的table组件，的set和get 
"""


def fill_data(table_widget, df):
    # 将dataframe的数据写入QTableWidget
    table_widget.setRowCount(df.shape[0])
    table_widget.setColumnCount(df.shape[1])
    table_widget.setHorizontalHeaderLabels(df.columns)
    for i in range(df.shape[0]):
        for j in range(df.shape[1]):
            table_widget.setItem(i, j, QTableWidgetItem(str(df.iloc[i, j])))


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
