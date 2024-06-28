import typing

import xlwings as xw

SHEET_TYPE = typing.Union[str, int]
SHEETS_TYPE = typing.List[SHEET_TYPE]


class ExcelStyleValue:
    def __init__(self, excel_path, sheet_name_or_index, run_mute=False):
        self.app = xw.App(visible=not run_mute, add_book=False)
        self.wb = self.app.books.open(excel_path)
        self.sht = self.wb.sheets[sheet_name_or_index]

        self.shts = []

    def for_each(self, func: typing.Callable[[str], None]):
        if not self.shts:
            print("没有存储批量的sheet，请先调用batch copy接口批量创建sheet")
        for sht in self.shts:
            self.sht = sht  # 改变当前self指向
            func(self.sht.name)
        return self

    def set_cell(self, cell, value, limit=True):
        if limit:
            self.sht.range(cell).value = value
        return self

    # 单元格操作：合并单元格
    def merge_cell(self, left_top, right_bottom):
        """
        :param left_top: (1,2)  表示第一行第二列
        :param right_bottom: 同上
        :return:
        """
        self.sht.range(left_top, right_bottom).api.MergeCells = True
        return self

    # 行操作：向下复制
    def copy_row_down(self, row_num: int, n=1, set_df=None, limit=True):
        """拷贝这一行往下，的n行，如果给了set_df，就用set_df的值填充拷贝出来的行
        :param row_num:
        :param n:
        :param set_df: 如果行数和拷贝出来的行数一样，只覆盖拷贝出来的行；如果行数比拷贝出来的多一行，那么连最开始的那一行也覆盖
        :param limit: 是否要拷贝
        :return:
        """
        if not limit:
            return self
        for i in range(n):  # 循环粘贴
            row = self.sht.range(f'{row_num}:{row_num}')
            row.api.Copy()  # 拷贝这一行
            self.sht.range(f'{row_num + i+1}:{row_num + i+1}').api.Insert()
        if set_df is not None:
            if n == len(set_df):
                for index, row in set_df.iterrows():
                    self.set_row(row_num + 1 + index, row.to_list())
            elif n == len(set_df) - 1:  # 说明要把最开始的那一行也覆盖掉
                for index, row in set_df.iterrows():
                    self.set_row(row_num + index, row.to_list())
        return self

    # 行操作：设置一行（保留样式）
    def set_row(self, row_num: int, value_list: typing.List[str]):
        self.sht.range(f'{row_num}:{row_num}').value = value_list
        return self

    # 行操作：删除一行（保留样式）
    def delete_row(self, row_num: int, limit=True):
        if limit:
            self.sht.range(f'{row_num}:{row_num}').api.Delete()
        return self

    # 行操作：删除一行（保留样式）
    def batch_delete_row(self, start_row_num: int, end_row_num: int, limit=True):
        if limit:
            self.sht.range(f'{start_row_num}:{end_row_num}').api.Delete()
        return self

    # 列操作：删除一列
    def delete_col(self, col_num: int, limit=True):
        if limit:
            self.sht.range((1, col_num)).api.EntireColumn.Delete()
        return self

    # sheet操作：重命名
    def rename_sheet(self, new_sheet_name: str):
        self.sht.name = new_sheet_name
        return self

    # sheet操作：重命名
    def batch_rename_sheet(self, sheet_name_mapping: typing.Dict[SHEET_TYPE, str]):
        """批量重命名sheet
        :param sheet_name_mapping:
            sheet_name_or_index : new_sheet_name
        :return:
        """
        for sheet_name_or_index, new_sheet_name in sheet_name_mapping.items():
            self.wb.sheets[sheet_name_or_index].name = new_sheet_name
        return self

    # sheet操作：拷贝
    def batch_copy_sheet(self, new_name_list: typing.List[str], del_old=False):
        """拷贝当前sheet到excel的最后（可以批量拷贝
        :param new_name_list: 可以拷贝多份
        :param del_old: 如果为True，拷贝完删除老的（剪切）
        :return:
        """
        for name in new_name_list:
            self.sht.api.Copy(After=self.wb.sheets[-1].api)
            self.wb.sheets[-1].name = name
            self.shts.append(self.wb.sheets[-1])
        old_sheet_name = self.sht.name
        if del_old:
            self.batch_delete_sheet([old_sheet_name])
        self.sht = self.wb.sheets[-1]
        return self

    def switch_sheet(self, sheet_name_or_index: SHEET_TYPE):
        self.sht = self.wb.sheets[sheet_name_or_index]
        return self

    # sheet操作：删除
    def batch_delete_sheet(self, sheet_name_or_index_list: SHEETS_TYPE):
        """将index全都先转成名字，如果有index
        :param sheet_name_or_index_list:
        """
        sheet_names = [sheet.name for sheet in self.wb.sheets]
        del_sheets = []
        for sheet_name_or_index in sheet_name_or_index_list:
            if isinstance(sheet_name_or_index, int):
                del_sheets.append(sheet_names[sheet_name_or_index])
            else:
                del_sheets.append(sheet_name_or_index)
        for del_sheet_name in set(del_sheets):
            self.wb.sheets[del_sheet_name].delete()
        return self

    def activate_sheet(self, sheet_name_or_index: SHEET_TYPE):
        """保存前可以修改激活的sheet到第一个，打开这个excel就是第一个了"""
        self.wb.sheets[sheet_name_or_index].activate()
        return self

    def save(self, path: str = None):
        # 保存为新的Excel文件
        if path is None:
            self.wb.save()
        else:
            self.wb.save(path)
        self.wb.close()

    def discard(self):
        self.wb.close()
