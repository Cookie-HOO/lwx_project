import pandas as pd

from lwx_project.utils.calculator import float2int


def get_window_of_df_as_df(df, x_range, y_range):
    """获取df的一个区域组成一个df
    :param df:
    :param x_range:
    :param y_range:
    :return:
    """
    if len(x_range) == 2 and len(y_range) == 2:
        data = df.iloc[x_range[0]:x_range[1], y_range[0]:y_range[1]]
        data.iloc[:, 3] = data.iloc[:, 3].apply(lambda x: str(float2int(x)) if not pd.isna(x) else '')
        return data
    return df
