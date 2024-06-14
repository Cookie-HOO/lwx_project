import math
import typing

import pandas as pd


def float2int(value) -> typing.Optional[int]:
    """四舍五入，python自带的四舍五入有些问题
    a = 0.5
    round(0.5)  # 0
    """
    if not isinstance(value, (float, int)):
        return None
    if value == 0:
        return 0
    elif value > 0:
        int_part = math.floor(value)
        float_part = value - int_part
        tail = 1 if float_part >= 0.5 else 0
        return int_part + tail
    elif value < 0:
        return -1 * float2int(-1 * value)


def num_or_na_or_zero(num):
    if pd.isna(num):
        return 0
    return num


if __name__ == '__main__':
    print(float2int(2.5))
    print(float2int(-2.5))
    print(float2int(0))


