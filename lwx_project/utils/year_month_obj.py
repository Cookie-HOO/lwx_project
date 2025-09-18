from datetime import date


class YearMonth:
    def __init__(self, year=None, month=None):
        today = date.today()
        year = year or today.year
        month = month or today.month
        self.year = year
        self.month = month

    @classmethod
    def new_from_str(cls, str_with_dash):
        if "-" in str_with_dash:
            parts = str_with_dash.split('-')
            if len(parts) == 2:
                year_str = parts[0]
                month_str = parts[1].lstrip('0')
                if year_str.isdigit() and month_str.isdigit():
                    year = int(year_str)
                    month = int(month_str)
                    return cls(year, month)
        return None

    def add_one_month(self):
        if self.month == 12:
            self.year += 1
            self.month = 1
        else:
            self.month += 1
        return self

    def sub_one_month(self):
        if self.month == 1:
            self.year -= 1
            self.month = 12
        else:
            self.month -= 1
        return self

    @property
    def str_with_dash(self):
        return f"{self.year}-{self.month:02d}"

    @property
    def str_with_only_number(self):
        return f"{self.year}{self.month:02d}"