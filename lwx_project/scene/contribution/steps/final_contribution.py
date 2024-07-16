import numpy as np
import pandas as pd

from lwx_project.utils.calculator import float2int, cal_increase


def main(df, alpha):
    # 1. 增加同比
    df["同比"] = df.apply(lambda row: cal_increase(now_value=row["期缴保费"], last_value=row["去年期缴保费"], value_when_div_zero="—", formatter="%"), axis=1)

    # 2. 计算贡献率
    df["贡献率"] = df["存量贡献率"] * alpha + df["增量贡献率"] * (1 - alpha)
    # df["贡献率"] = df["贡献率"] / df["贡献率"].sum()
    df = df.sort_values(by=['贡献率'], ascending=False)
    df["__贡献率"] = df["贡献率"]

    # 3. 增加合计
    summary_cur = df["期缴保费"].sum() - df["期缴保费"].mean()
    summary_last = df["去年期缴保费"].sum() - df["去年期缴保费"].mean()
    summary_increase = (summary_cur - summary_last) / summary_last
    summary = pd.DataFrame({
        '公司': ["合计"],
        '期缴保费': [summary_cur],
        '去年期缴保费': [summary_last],
        '同比': [str(round(summary_increase * 100, 1)) + '%'],
        '增量': [summary_cur - summary_last],
        # '贡献率': [str(round(df["贡献率"].sum() * 100, 1)) + '%'],
        # "__贡献率": [df["__贡献率"].sum()],

        '贡献率': [''],
        "__贡献率": [0]
    })

    # 4. % 处理
    df["贡献率"] = df["贡献率"].apply(lambda x: str(round(x*100, 1)) + '%')
    df.replace('nan%', 0, inplace=True)  # 似乎没用了
    df.replace('inf%', 0, inplace=True)  # 似乎没用了
    df.replace('0.0%', 0, inplace=True)

    # 5. 整理结果
    df = pd.concat([df, summary], axis=0, ignore_index=True)
    df["期缴保费"] = df["期缴保费"].apply(lambda x: float2int(x))
    df["去年期缴保费"] = df["去年期缴保费"].apply(lambda x: float2int(x))
    df["增量"] = df["增量"].apply(lambda x: float2int(x))

    return df
