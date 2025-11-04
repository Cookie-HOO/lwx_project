import datetime
from datetime import date


class YearMonth:
    def __init__(self, year=None, month=None):
        today = date.today()
        year = year or today.year
        month = month or today.month
        self.year = year
        self.month = month

    # as key in dict
    def __eq__(self, other):
        return isinstance(other, YearMonth) and self.year == other.year and self.month == other.month

    def __hash__(self):
        return hash((self.year, self.month))

    def __lt__(self, other):
        # 定义比较逻辑，比如按 x 坐标比较，x 相同则按 y 比较
        if self.year != other.year:
            return self.year < other.year
        return self.month < other.month

    @classmethod
    def new_from_str(cls, str_with_dash_or_digit):
        split = None
        if isinstance(str_with_dash_or_digit, str):
            if "-" in str_with_dash_or_digit:
                split = "-"
            elif "/" in str_with_dash_or_digit:
                split = "/"

            elif str_with_dash_or_digit.isdigit() and len(str_with_dash_or_digit) == 6:
                year = int(str_with_dash_or_digit[:4])
                month = int(str_with_dash_or_digit[4:].strip('0'))
                return cls(year, month)

        elif isinstance(str_with_dash_or_digit, datetime.datetime):
            return cls(year=str_with_dash_or_digit.year, month=str_with_dash_or_digit.month)

        # split
        if split is not None:
            parts = str_with_dash_or_digit.split(split)
            if parts and len(parts) >= 2:
                year_str = parts[0]
                month_str = parts[1].lstrip('0')
                if year_str.isdigit() and month_str.isdigit():
                    year = int(year_str)
                    month = int(month_str)
                    return cls(year, month)
        return None

    def add_one_month(self):
        if self.month == 12:
            return YearMonth(self.year+1, 1)
        else:
            return YearMonth(self.year, self.month+1)

    def sub_one_month(self):
        if self.month == 1:
            return YearMonth(self.year-1, 12)
        else:
            return YearMonth(self.year, self.month-1)

    @property
    def str_with_dash(self):
        return f"{self.year}-{self.month:02d}"

    @property
    def str_with_only_number(self):
        return f"{self.year}{self.month:02d}"

    @property
    def max_day_of_month(self) -> int:
        # 下个月的第一天-1 的day 就是当前月天的最大值
        first_date_of_next_month = date(int(self.year), self.month+1, 1)
        last_date_of_this_month = first_date_of_next_month - datetime.timedelta(days=1)
        return last_date_of_this_month.day
