import pandas as pd

from lwx_project.utils.file import get_file_name_without_extension


class ExcelCheckWrapper:
    def __init__(self, excel_path, sheet_name_or_index=None):
        # 参数
        self._excel_path = excel_path
        self._sheet_name_or_index = sheet_name_or_index

        # 读取
        self.xls = pd.ExcelFile(excel_path)
        if sheet_name_or_index:
            self.df = pd.read_excel(excel_path, sheet_name=sheet_name_or_index)
        else:
            self.df = pd.read_excel(excel_path)

        # 校验
        self._base_name = get_file_name_without_extension(excel_path)
        self._passed = True
        self._reason = ""

    def reset(self, excel_path=None, sheet_name_or_index=None):
        # 切换excel
        if excel_path:
            self.xls = pd.ExcelFile(excel_path)
            self._base_name = get_file_name_without_extension(excel_path)

        # 切换df
        if excel_path or sheet_name_or_index:
            excel_path = excel_path or self._excel_path
            self.df = pd.read_excel(excel_path, sheet_name=sheet_name_or_index)

        # 只要有切换，重置条件
        if excel_path or sheet_name_or_index:
            self._passed = True
            self._reason = ""
        return self

    def has_cols(self, cols: list) -> 'ExcelCheckWrapper':
        for col in cols:
            if not self._passed:
                return self
            if col not in self.df.columns:
                self._reason = f"【{self._base_name}】没有列：{col}"
                self._passed = False
                return self
        return self

    def has_sheets(self, sheets: list) -> 'ExcelCheckWrapper':
        if not self._passed:
            return self
        for sheet in sheets:
            if not self._passed:
                return self
            if sheet not in self.xls.sheet_names:
                self._reason = f"【{self._base_name}】没有sheet：{sheet}"
                self._passed = False
                return self
        return self

    def has_values(self, values, col=None, row=None) -> 'ExcelCheckWrapper':
        if not self._passed:
            return self
        for value in values:
            if not self._passed:
                return self
            if col:
                if value not in self.df[col].values:
                    self._reason = f"【{self._base_name}】的【{col}】列没有值{value}"
                    self._passed = False
                    return self
            if row:
                if value not in self.df.iloc[row].values:
                    self._reason = f"【{self._base_name}】文件的【{row+2}】行没有值{value}"
                    self._passed = False
                    return self
        return self

    def no_dup_values(self, col) -> 'ExcelCheckWrapper':
        if not self._passed:
            return self

        duplicates = self.df[self.df[col].duplicated()][col].to_list()
        if duplicates:
            self._reason = f"{self._base_name}的列{col}存在重复值{duplicates}"
            self._passed = False
        return self

    def check_all_pass(self) -> bool:
        return self._passed

    def check_any_failed(self) -> bool:
        return not self._passed

    @property
    def reason(self):
        return self._reason
