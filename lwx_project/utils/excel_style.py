import os
import re
import typing

import xlwings as xw

SHEET_TYPE = typing.Union[str, int]
SHEETS_TYPE = typing.List[SHEET_TYPE]


class ExcelStyleValue:
    def __init__(self, excel_path, sheet_name_or_index=0, run_mute=False):
        self.excel_path = excel_path
        self.app = xw.App(visible=not run_mute, add_book=False)
        self.wb = self.app.books.open(excel_path)
        self.sht = self.wb.sheets[sheet_name_or_index]
        self.shts_length = len(self.wb.sheets)

        self.shts = []

    def for_each_sheet(self, func: typing.Callable[[str], None]):
        """遍历存储的sheets，遇到batch_copy时会存储"""
        if not self.shts:
            print("没有存储批量的sheet，请先调用batch copy接口批量创建sheet")
        for sht in self.shts:
            self.sht = sht  # 改变当前self指向
            func(self.sht.name)
        return self

    def get_cell(self, cell):
        return self.sht.range(cell).value

    def set_cell(self, cell, value, limit=True):
        if limit:
            self.sht.range(cell).value = value
        return self

    # 单元格操作：合并单元格
    def merge_cell(self, left_top, right_bottom, limit=True):
        """
        :param left_top: (1,2)  表示第一行第二列
        :param right_bottom: 同上
        :param limit: 同上
        :return:
        """
        if limit:
            self.sht.range(left_top, right_bottom).api.MergeCells = True
        return self

    def update_text_shape(self, pattern2text: typing.Dict[str, str]):
        """修改当前sheet下的文本框中的文字
        pattern2text: 正则表达式 -> 修改的文字
        """
        for shape in self.sht.shapes:
            try:
                # 尝试读取文本（如果是文本框或包含文本的形状）
                current_text = shape.text
                for p, t in pattern2text.items():
                    if re.match(p, current_text):
                        shape.text = t
            except Exception as e:
                # 不是文本框（比如是图片、图表等），跳过
                continue
        return self

    def get_style(self, cell):
        obj = self.sht.range(cell)
        return {
            "bg_color": obj.color,  # 背景色
            "font_color": obj.font.color,
            "font_bold": obj.font.bold,
            "font_italic": obj.font.italic,
            "font_family": obj.font.name,
            "font_size": obj.font.size,
            "column_width": obj.column_width,
            "row_height": obj.height,
            "formula": obj.formula,
            "number_format": obj.number_format,
            "value": obj.value,
            "raw_value": obj.raw_value,
        }
    # 样式
    def set_style(self, range_text, bg_color, font_color, bold):
        """
        range_text: "A1:C10"  范围
        bg_color: (255, 255, 255)  白色
        font_color: (0, 0, 255)   黑色
        bold: 是否加粗
        """
        rng = self.sht.range(range_text)

        # 1. 设置背景色（RGB 或颜色名称）
        rng.color = bg_color  # 浅红色 (R, G, B)
        # 或使用十六进制（部分版本支持）：
        # rng.color = "#FFC8C8"

        # 2. 设置字体颜色
        rng.font.color = font_color  # 蓝色

        # 3. 设置字体加粗
        rng.font.bold = bold
        return self

    def range_sort(self, col_num, range_text, desc=False):
        """
        手动排序：读取数据 → 按指定列排序 → 写回

        :param col_num: 排序列在 range_text 中的位置（从1开始）
        :param range_text: 排序范围，如 "A3:J25"
        :param desc: False=升序，True=降序
        """
        # 1. 读取整个区域的值（二维列表）
        rng = self.sht.range(range_text)
        original_data = rng.value  # list of lists

        # 处理单行情况（xlwings 返回一维列表）
        if isinstance(original_data[0], (int, float, str, type(None))):
            original_data = [original_data]

        # 2. 提取排序列的值（col_num 从1开始 → 索引 col_num-1）
        sort_col_index = col_num - 1
        try:
            sort_values = [row[sort_col_index] for row in original_data]
        except IndexError:
            raise ValueError(f"列号 {col_num} 超出范围，区域 {range_text} 最大列数为 {len(original_data[0])}")

        # 3. 生成排序索引
        # 使用 enumerate 保留原始行号，按值排序
        indexed_rows = list(enumerate(sort_values))

        # 定义排序 key：处理 None / 空值（放到最后）
        def sort_key(item):
            idx, val = item
            # 将 None / 空字符串视为无穷大（排最后）
            if val is None or val == "":
                return (float('inf'), "")
            # 如果是数字，直接比较；如果是字符串，转为小写
            if isinstance(val, (int, float)):
                return (val, "")
            else:
                return (str(val).lower(), val)

        indexed_rows.sort(key=sort_key, reverse=desc)

        # 4. 按排序后的索引重排所有行
        sorted_data = [original_data[idx] for idx, _ in indexed_rows]

        # 5. 写回 Excel
        rng.value = sorted_data

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

    def copy_col(self, from_col_num: int, to_col_num, limit=True):
        if not limit:
            return self
        from_col_alpha = self.num2col_char(from_col_num)
        to_col_alpha = self.num2col_char(to_col_num)
        col = self.sht.range(f'{from_col_alpha}:{from_col_alpha}')
        col.api.Copy()
        self.sht.range(f'{to_col_alpha}:{to_col_alpha}').api.Insert()
        return self

    # 行操作：设置一行（保留样式）
    def set_row(self, row_num: int, value_list: typing.List[str]):
        self.sht.range(f'{row_num}:{row_num}').value = value_list
        return self

    def set_col_by_values(self, col_num: int, values: typing.List[str], start_row_num: int = 1):
        """"""
        if len(values) <= 0:
            return self
        start_row_num = start_row_num or 1
        row_nums = range(start_row_num, start_row_num + len(values))
        for row_num, value in zip(row_nums, values):
            self.set_cell((row_num, col_num), value)
        return self

    def set_col_by_col(self, from_col, to_col, start_row_num=1, end_row_num: int = None, end_format: typing.Callable=None):
        start_col_char = self.num2col_char(from_col)
        if end_row_num is None:
            start = f"{start_col_char}1"
            end_row_num = self.sht.range(start).end('down').row
        values = self.sht.range(f"{start_col_char}{start_row_num}:{start_col_char}{end_row_num}").value
        if end_format:
            values = [end_format(i) for i in values]
        self.set_col_by_values(to_col, values, start_row_num=start_row_num)
        return self

    def get_col(self, col_num: int, start_row_num: int, end_row_num: int = None):
        col_alpha = self.num2col_char(col_num)
        col = self.sht.range(f'{col_alpha}:{col_alpha}')
        return col.value

        col.api.Copy()


        values = []
        if end_row_num is None:
            start = f"{self.num2col_char(col_num)}1"
            end_row_num = self.sht.range().end('down').row

        values = [self.get_cell((start_row_num, col_num))]
        return values

    # 行操作：删除一行（保留样式）
    def delete_row(self, row_num: int, limit=True):
        if limit:
            self.sht.range(f'{row_num}:{row_num}').api.Delete()
        return self

    # 行操作：删除多行（保留样式）
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
    def batch_copy_sheet(self, new_name_list: typing.List[str], append=True, del_old=False):
        """拷贝当前sheet到excel的最后（可以批量拷贝
        :param new_name_list: 可以拷贝多份
        :param append: 如果为True，往后拷贝，结束后，最后一个是activate的；如果是False，从第一个往前拷贝，结束后第一个是activate的
        :param del_old: 如果为True，拷贝完删除老的（剪切）
        :return:
        """
        old_sheet_name = self.sht.name
        if append:
            for name in new_name_list:
                self.sht.api.Copy(After=self.wb.sheets[-1].api)
                self.wb.sheets[-1].name = name
                self.shts.append(self.wb.sheets[-1])
            self.sht = self.wb.sheets[-1]
        else:
            for name in new_name_list:
                self.sht.api.Copy(Before=self.wb.sheets[0].api)
                self.wb.sheets[0].name = name
                self.shts.append(self.wb.sheets[0])
            self.sht = self.wb.sheets[0]
        if del_old:
            self.batch_delete_sheet([old_sheet_name])
        return self

    # sheet操作：新建
    def new_sheet(self, sheet_name_or_index: SHEET_TYPE, before_name=None, after_name=None):
        if before_name is None and after_name is None:
            self.wb.sheets.add(sheet_name_or_index)
            return self.wb.sheets[sheet_name_or_index]
        elif before_name:
            self.wb.sheets.add(sheet_name_or_index, before=self.wb.sheets[before_name])
        elif after_name:
            self.wb.sheets.add(sheet_name_or_index, after=self.wb.sheets[after_name])
        self.sht = self.wb.sheets[sheet_name_or_index]
        return self

    # sheet操作：切换
    def switch_sheet(self, sheet_name_or_index: SHEET_TYPE):
        self.sht = self.wb.sheets[sheet_name_or_index]
        # 这里无法使用activate，需要excel可见
        # self.wb.sheets[sheet_name_or_index].activate()
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

    def batch_delete_sheet_except(self, sheet_name_or_index_list: typing.List[SHEET_TYPE]):
        sheet_names = [sheet.name for sheet in self.wb.sheets]
        not_del_sheets = []
        for sheet_name_or_index in sheet_name_or_index_list:
            if isinstance(sheet_name_or_index, int):
                not_del_sheets.append(sheet_names[sheet_name_or_index])
            else:
                not_del_sheets.append(sheet_name_or_index)
        for sheet_name in sheet_names:
            if sheet_name not in set(not_del_sheets):
                self.wb.sheets[sheet_name].delete()
        return self


    def activate_sheet(self, sheet_name_or_index: SHEET_TYPE):
        """保存前可以修改激活的sheet到第一个，打开这个excel就是第一个了"""
        self.wb.sheets[sheet_name_or_index].activate()
        return self

    # sheet操作：清空所有
    def sheet_clear(self):  # 清空所有内容和格式
        self.sht.clear()
        return self

    # sheet操作：仅清空内容，保留格式
    def sheet_clear_contents(self):  # 只清空内容，保留格式
        self.sht.clear_contents()
        return self

    # sheet操作：删除指定sheet
    def del_sheet(self, sheet_name_or_index: SHEET_TYPE):
        # 通过名称删除特定工作表
        self.wb.sheets[sheet_name_or_index].delete()
        return self

    def sheet_copy_from_other_excel(self, other_excel_path: str = None, other_excel_sheet_name: str = None):
        """将其他excel文件或者当前excel的某个sheet，拷贝到当前sheet"""
        other_wb = self.wb
        if other_excel_sheet_name is None:
            other_wb = self.app.books.open(other_excel_path)
        self.sheet_clear()
        other_excel_sheet_name = other_excel_sheet_name or 0
        used_range = other_wb.sheets[other_excel_sheet_name].used_range
        # 如果源工作表有内容，则复制
        if used_range is not None:
            # 复制源数据到目标工作表的相同位置
            self.sht.range(used_range.address).value = used_range.value
        if other_excel_path:
            other_wb.close()
        return self

    # sheet操作：保存成新的excel
    def copy2new_excel(self, output_path):
        app = xw.App(visible=False)  # visible=True 可看到 Excel 窗口
        wb = app.books.add()  # 新建工作簿，默认有 Sheet1
        sheet = wb.sheets[0]
        used_range = self.sht.used_range
        if used_range is not None:
            sheet.range(used_range.address).value = used_range.value

        # 保存为文件
        wb.save(output_path)
        wb.close()
        app.quit()

        return self

    def save(self, path: str = None):
        # 保存为新的Excel文件
        self.excel_path = None
        if path is None:
            self.wb.save()
        else:
            self.wb.save(path)
        self.wb.close()

    def discard(self):
        self.wb.close()

    @staticmethod
    def num2col_char(num: int) -> str:
        """1 -> A"""
        chars = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        if num > 26:
            raise ValueError("more than 26")
        return chars[num-1]
