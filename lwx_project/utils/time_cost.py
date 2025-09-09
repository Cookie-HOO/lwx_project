# 统计耗时的装饰器
import functools
import time


def time_cost(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} cost: {end - start}")
        return result
    return inner