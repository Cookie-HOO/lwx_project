import typing

from lwx_project.utils.high_performance import FastExcelReader
from lwx_project.utils.year_month_obj import YearMonth

"""
业务工具函数，和具体业务强相关，跨业务场景的工具函数放在这里
"""

def core_tuanxian_get_month(detail_path: str) -> typing.Optional[YearMonth]:
    """核心团险表：经常需要读取，写一个专门的工具函数来处理 日期问题
    高效读取 Excel 文件前两行：
    - 第一行：列名，查找「日期」列
    - 找到日期列对应的第二行数据，提取日期值
    返回 datetime.date 对象。
    """
    with FastExcelReader(detail_path) as fe:
        col_num = fe.posit_col_in_row_by_value(row_num=1, value="日期")
        date_value = fe.get_cell_value(2, col_num)
        if date_value:
            return YearMonth.new_from_str(date_value)