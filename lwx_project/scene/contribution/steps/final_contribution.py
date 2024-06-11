def main(df, alpha):
    df["贡献率"] = df["存量贡献率"] * alpha + df["增量贡献率"] * (1 - alpha)
    df["贡献率"] = df["贡献率"] / df["贡献率"].sum()
    df = df.sort_values(by=['贡献率'], ascending=False)
    df["贡献率"] = df["贡献率"].apply(lambda x: str(round(x*100, 4)) + '%')
    return df[["公司", "期缴保费", "去年期缴保费", "增量", "贡献率"]]
