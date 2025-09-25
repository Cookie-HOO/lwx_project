import typing
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter


class FastExcelReader:
    """基于openpyxl 直接读取excel指定内容

    用法一：推荐
    with FastExcelReader(file_path) as fe:
        c = fe.get_excel_column_count(max_col_num=3)

    用法二
    try:
        fe = FastExcelReader(file_path)
        c = fe.get_excel_column_count(max_col_num=3)
    finally:
        fe.close()
    """

    MAX_COL_NUM = 16384  # 安全上限：Excel 最大列数为 16384 (XFD)

    def __init__(self, file_path: str, sheet_name: typing.Optional[str] = None):
        self.file_path = file_path
        self.sheet_name = sheet_name
        self.wb = load_workbook(self.file_path, read_only=True)
        self.ws = self.wb.active if self.sheet_name is None else self.wb[self.sheet_name]

    def __enter__(self):
        # 打开工作簿（只读模式，高效）
        return self  # 返回自身，供 with 块内使用

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 无论是否发生异常，都关闭工作簿
        self.close()
        # 返回 False 表示不抑制异常（推荐）
        return False

    def close(self):
        self.wb.close()

    def get_excel_column_count(self, max_col_num=None, row_num=1) -> int:
        """获取 Excel 文件中连续非空列的数量（从 A1 开始向右，遇到第一个空单元格即停止）。

        注意：此方法假设“列是连续的”，一旦遇到空单元格就停止计数，
        即使后续列有数据也不会被计入。

        参数:
            max_col_num (int, optional): 最多检查到第几列。
            row_num (int, optional): 用第几行作为标准计算列的个数
        返回:
            int: 第一行从左到右连续非空单元格的数量（至少为 0）。
        """
        col_index = 1
        max_col_num = max_col_num or self.MAX_COL_NUM
        try:
            while True:
                col_letter = get_column_letter(col_index)
                cell_value = self.ws[f"{col_letter}{row_num}"].value
                # None or ""
                if cell_value is None or (isinstance(cell_value, str) and len(cell_value) == 0):
                    break
                col_index += 1
                if col_index > max_col_num:
                    break
        finally:
            return col_index - 1


    def check_excel_row(self, row_num, required_value_list: list, max_col_num=None) -> (typing.Optional[int], list):
        max_col_num = max_col_num or self.MAX_COL_NUM
        required_value_list_copy = required_value_list[:]
        col_index = 1

        try:
            while required_value_list_copy:
                col_letter = get_column_letter(col_index)
                cell_value = self.ws[f"{col_letter}{row_num}"].value
                # None or ""
                if cell_value is None or (isinstance(cell_value, str) and len(cell_value) == 0):
                    pass
                else:
                    if cell_value in required_value_list_copy:
                        required_value_list_copy.remove(cell_value)
                col_index += 1
                if col_index > max_col_num:
                    break
        finally:
            return len(required_value_list_copy) == 0, required_value_list_copy