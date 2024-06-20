import datetime
import math

from lwx_project.const import FULL_TIME_FORMATTER, DATE_FORMATTER, TIME_FORMATTER


class TimeObj:
    def __init__(self, raw_time_str=None, equal_buffer=0):
        self.raw_time_str = raw_time_str
        self.today = datetime.datetime.today()
        self.equal_buffer = equal_buffer

    @property
    def date_str(self):
        if not self.raw_time_str:
            return self.today.strftime(DATE_FORMATTER)
        time_str_ = self.raw_time_str
        if self.raw_time_str.isdigit() and len(self.raw_time_str) == 8:
            time_str_ = self.raw_time_str[:4] + "-" + self.raw_time_str[4:6] + "-" + self.raw_time_str[6:]
        elif "年" in self.raw_time_str and "月" in self.raw_time_str and "日" in self.raw_time_str:
            time_str_ = self.raw_time_str.replace("年", "-").replace("月", "-").replace("日", "")
        return time_str_

    @property
    def full_time_str(self):
        if not self.raw_time_str:
            return self.today.strftime(FULL_TIME_FORMATTER)
        return self.time_obj.strftime(FULL_TIME_FORMATTER)

    @property
    def time_str(self):
        if not self.raw_time_str:
            return self.today.strftime(TIME_FORMATTER)
        return self.time_obj.strftime(TIME_FORMATTER)

    @property
    def time_obj(self):
        if not self.raw_time_str:
            return self.today
        return datetime.datetime.strptime(self.date_str, DATE_FORMATTER)

    def __eq__(self, other):
        return abs((self.time_obj - other.time_obj).days) <= self.equal_buffer

    def __gt__(self, other):
        return self.time_obj > other.time_obj

    def __lt__(self, other):
        return self.time_obj < other.time_obj

    @property
    def month_day(self):
        date_str = self.date_str
        if not date_str:
            return ""
        return "-".join(date_str.split("-")[-2:])

    @property
    def year(self) -> int:
        return self.time_obj.year

    @property
    def month(self) -> int:
        return self.time_obj.month

    @property
    def day(self) -> int:
        return self.time_obj.day

    @property
    def season(self) -> int:
        return math.ceil(self.month / 3)

    @property
    def season_in_char(self) -> str:
        mapping = {1: "一", 2: "二", 3: "三", 4: "四"}
        return mapping.get(self.season)

    @property
    def until_last_season(self) -> str:
        # 前三季度、前两季度、一季度、1-12月
        season_num = self.season
        if season_num == 1:
            return f"{self.year-1}年1-12月"
        elif season_num == 2:
            return f"{self.year}年一季度"
        elif season_num == 3:
            return f"{self.year}年前两季度"
        elif season_num == 4:
            return f"{self.year}年前三季度"

    @property
    def is_first_day_of_this_year(self):
        return self.year == self.today.year and self.month == 1 and self.day == 1

    @property
    def is_first_day_of_this_season(self):
        season_month = self.today.month - (self.today.month - 1) % 3
        return self.year == self.today.year and self.month == season_month and self.day == 1

    @property
    def is_first_day_of_this_month(self):
        return self.year == self.today.year and self.month == self.today.month and self.day == 1
