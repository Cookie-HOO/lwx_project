import numpy as np
import pandas as pd


def main(df, alpha):
    # 1. 增加同比
    df["同比"] = (df["期缴保费"] - df["去年期缴保费"]) / df["去年期缴保费"]
    df['同比'].fillna(0, inplace=True)
    df['同比'].replace(np.inf, 0, inplace=True)

    # 2. 计算贡献率
    df["贡献率"] = df["存量贡献率"] * alpha + df["增量贡献率"] * (1 - alpha)
    df["贡献率"] = df["贡献率"] / df["贡献率"].sum()
    df = df.sort_values(by=['贡献率'], ascending=False)

    # 3. 增加合计
    summary_cur = df["期缴保费"].sum()
    summary_last = df["去年期缴保费"].sum()
    summary_increase = (summary_cur - summary_last) / summary_last
    summary = pd.DataFrame({
        '公司': ["合计"],
        '期缴保费': [summary_cur],
        '去年期缴保费': [summary_last],
        '增量': [df["增量"].sum()],
        '贡献率': [str(round(df["贡献率"].sum() * 100, 1)) + '%'],
        '同比': [str(round(summary_increase * 100, 1)) + '%'],
    })

    # 4. % 处理
    df["贡献率"] = df["贡献率"].apply(lambda x: str(round(x*100, 1)) + '%')
    df["同比"] = df["同比"].apply(lambda x: str(round(x * 100, 1)) + '%')
    df.replace('nan%', 0, inplace=True)  # 似乎没用了
    df.replace('inf%', 0, inplace=True)  # 似乎没用了
    df.replace('0.0%', 0, inplace=True)

    # 5. 整理结果
    df = df.append(summary, ignore_index=True)
    df["期缴保费"] = df["期缴保费"].apply(lambda x: round(x))
    df["去年期缴保费"] = df["去年期缴保费"].apply(lambda x: round(x))
    df["增量"] = df["增量"].apply(lambda x: round(x))

    return df[["公司", "期缴保费", "去年期缴保费", "同比", "增量", "贡献率"]]
