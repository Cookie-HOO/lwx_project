def cal_increase_contribution(value, threshold, min_, max_):
    diff = value - threshold
    if diff < 0:
        return diff / (threshold - min_)
    elif diff > 0:
        return diff / (max_ - threshold)
    return 0


def main(df):
    df["增量"] = df["期缴保费"] - df["去年期缴保费"]
    avg_increase = df["增量"].mean()
    min_ = df["增量"].min()
    max_ = df["增量"].max()
    # df["增量贡献量"] = df["增量"] - avg_increase
    #
    # max_increase = df["增量贡献量"].max()
    # min_increase = df["增量贡献量"].min()
    df["增量贡献率"] = df["增量"].apply(lambda x: cal_increase_contribution(x, avg_increase, min_, max_))
    return df
