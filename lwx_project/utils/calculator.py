import math

import pandas as pd


def my_round(num, sig=0):
    if sig == 0:
        if num == 0:
            return 0
        elif num > 0:
            tail = 1 if num >= 0.5 else 0
            return math.floor(num) + tail
        elif num < 0:
            return -1 * my_round(-1*num)
        else:
            return num



def num_or_na_or_zero(num):
    if pd.isna(num):
        return 0
    return num


if __name__ == '__main__':
    print(my_round(2.5))
    print(my_round(-2.5))
    print(my_round(0))


