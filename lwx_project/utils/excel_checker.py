import os.path
import typing

import pandas as pd

from lwx_project.utils.file import get_file_name_with_extension
from lwx_project.utils.lazy_class import lazy


def must_has_df(origin_func):
    def wrapper(self: 'ExcelCheckerWrapper', *args, **kwargs):
        if self.df is None:
            return self
        return origin_func(self, *args, **kwargs)
    return wrapper


class ExcelCheckerWrapper:
    def __init__(self, excel_path, sheet_name_or_index=None, skiprows: int = 0, col_width=1, cols=None, skip_check_if=False):
        # 初始化校验list
        self._failed_reason = []

        # 读取前设置
        self._excel_path = excel_path
        self._sheet_name_or_index = sheet_name_or_index
        self._skiprows = skiprows
        self._col_width = col_width
        self._cols = cols
        # 读取结果设置
        self.xls = None
        self.df = None
        self.switch_dfs = []
        self._base_name = ""
        # 读取
        if not skip_check_if:
            self.init_file()

    @lazy.transformer
    def init_file(self) -> typing.Optional[pd.DataFrame]:
        """调用之前，必须赋值self._excel_path | self._sheet_name_or_index | self.skiprows"""
        # 读取excel
        self._base_name = get_file_name_with_extension(self._excel_path)
        if not os.path.exists(self._excel_path):
            self._failed_reason.append(f"文件无法找到")
            return
        self.xls = pd.ExcelFile(self._excel_path)

        # 读取sheet
        if self._sheet_name_or_index is not None:
            if isinstance(self._sheet_name_or_index, int):
                if self._sheet_name_or_index > len(self.xls.sheet_names) - 1:
                    self._failed_reason.append(f"没有指定index的工作表")
                    return
            elif isinstance(self._sheet_name_or_index, str):
                if self._sheet_name_or_index not in self.xls.sheet_names:
                    self._failed_reason.append(f"没有指定名称: [{self._sheet_name_or_index}] 的工作表")
                    return
        try:
            df = pd.read_excel(self._excel_path, sheet_name=self._sheet_name_or_index or 0, skiprows=self._skiprows, header=None)
            assert df is not None
        except Exception as e:
            self._failed_reason.append(f"读取失败: {str(e)}")
            return

        # 处理列头
        rows, cols = df.shape
        if self._col_width > rows:
            self._failed_reason.append(f"只有{rows}行，要求列宽{self._col_width}")
            return
        if self._col_width == 1:
            new_columns = df.iloc[0, :].ffill()
        elif self._col_width == 2:
            new_columns = df.iloc[0, :].ffill() + df.iloc[1, :].fillna(value='')
        else:
            raise ValueError("不支持 超过2行的col")
        df.columns = new_columns
        df.drop(index=list(range(self._col_width)), inplace=True)
        df.reset_index(inplace=True)
        if self._cols is not None:
            if self.has_cols(self._cols).check_any_failed():
                return
            df = df[self._cols]

        df.columns = df.columns.map(lambda x: x.replace("\n", "").replace(" ", ""))
        # 如果存在重复的列，那么取第一个列，去掉后面的重复列
        if len(list(df.columns)) != len(set(df.columns)):
            df = df.loc[:, ~df.columns.duplicated()]
        if df is None:
            self._failed_reason.append(f"读取失败")
            return
        self.df = df

    @lazy.transformer
    def switch(self, excel_path=None, sheet_name_or_index=None, skiprows: int = 0, col_width=1, cols=None, limit=True):
        assert sheet_name_or_index is not None  # 必须设置
        self.switch_dfs.append(self.df)
        self._excel_path = excel_path or self._excel_path
        self._sheet_name_or_index = sheet_name_or_index
        self._skiprows = skiprows
        self._col_width = col_width
        self._cols = cols
        if limit:
            self.init_file.__wrapped__(self)  # 这里需要立刻执行，不能等懒执行
        return self

    @lazy.transformer
    def row_process(self, row_num, process_func: typing.Callable[[str], str]):
        # todo: 这里行的顺序，num从哪里开始算
        # 预校验
        rows, cols = self.df.shape
        if row_num is not None:
            if row_num <= 0 or row_num > rows:
                self._failed_reason.append(f"只有{rows}行，没有第{row_num}行")

        self.df.loc[row_num-1] = self.df.loc[row_num-1].apply(process_func)
        return self

    @lazy.transformer
    def column_name_process(self, process_func: typing.Callable[[str], str]):
        self.df.columns = self.df.columns.map(process_func)
        return self

    @lazy.transformer
    def has_sheets(self, sheets: list) -> 'ExcelCheckerWrapper':
        for sheet in sheets:
            if sheet not in self.xls.sheet_names:
                self._failed_reason.append(f"没有指定工作表：{sheet}")
        return self

    @lazy.transformer
    def has_cols(self, cols: list, skip_check_if=False) -> 'ExcelCheckerWrapper':
        if not skip_check_if:
            for c in cols:
                if c not in self.df.columns:
                    self._failed_reason.append(f"没有指定列：{c}")
        return self

    @lazy.transformer
    def has_values(self, values, col_num_or_name=None, row_num=None) -> 'ExcelCheckerWrapper':
        # 预校验
        rows, cols = self.df.shape
        if col_num_or_name is not None:
            if isinstance(col_num_or_name, int):
                if col_num_or_name <= 0 or col_num_or_name > cols:
                    self._failed_reason.append(f"只有{cols}列，没有第{col_num_or_name}列")
            elif isinstance(col_num_or_name, str):
                if col_num_or_name not in self.df.columns:
                    self._failed_reason.append(f"没有第{col_num_or_name}列")
        if row_num is not None:
            if row_num <= 0 or row_num > rows:
                self._failed_reason.append(f"只有{rows}行，没有第{row_num}行")

        # 校验数值
        for value in values:
            if col_num_or_name is not None:
                if isinstance(col_num_or_name, int):
                    if value not in self.df.iloc[:, col_num_or_name-1].values:
                        self._failed_reason.append(f"第{col_num_or_name}列没有值{value}")
                if isinstance(col_num_or_name, str):
                    if value not in self.df[col_num_or_name].values:
                        self._failed_reason.append(f"{col_num_or_name}列没有值{value}")
            if row_num is not None:
                if value not in self.df.iloc[row_num-1].values:
                    self._failed_reason.append(f"第{row_num}行没有值{value}")
        return self

    @lazy.transformer
    def no_dup_values(self, col) -> 'ExcelCheckerWrapper':
        duplicates = self.df[self.df[col].duplicated()][col].to_list()
        if duplicates:
            self._failed_reason.append(f"列{col}存在重复值{duplicates}")
        return self

    @lazy.action
    def check_all_pass(self) -> bool:
        self.switch_dfs.append(self.df)
        return len(self._failed_reason) == 0

    @lazy.action
    def check_any_failed(self) -> bool:
        self.switch_dfs.append(self.df)
        return len(self._failed_reason) > 0

    @property
    def reason(self) -> list:
        reason_list = []
        for r in self._failed_reason:
            if "工作表" in r:
                reason_list.append(f"[{self._base_name}]: {r}")
            else:
                reason_list.append(f"[{self._base_name}]的工作表[{self._sheet_name_or_index}]: {r}")
        return reason_list


