from datetime import datetime, timedelta


def add_days_skip_weekends(start_date: str, days: int) -> str:
    """
    在基础时间上增加 days 天，跳过周末（周六、周日）

    :param start_date: 开始日期，格式为 'yyyy-MM-DD'
    :param days: 要增加的工作日天数（正整数）
    :return: 结果日期，格式为 'yyyy-MM-DD'
    """
    # 将字符串转换为 datetime 对象
    current_date = datetime.strptime(start_date, "%Y-%m-%d")

    added_days = 0

    while added_days < days:
        # 每次加一天
        current_date += timedelta(days=1)
        # 检查是否是工作日（周一到周五），weekday() 返回 0=周一, 6=周日
        if current_date.weekday() < 5:  # 排除周六(5)和周日(6)
            added_days += 1

    # 返回格式化后的字符串
    return current_date.strftime("%Y-%m-%d")
