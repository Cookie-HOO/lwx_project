def cal_increase_contribution(value, threshold, min_, max_):
    diff = value - threshold
    if diff < 0:
        return diff / (threshold - min_)
    elif diff > 0:
        return diff / (max_ - threshold)
    return 0


def main(df):
    mean = df['期缴保费'].mean()
    min_ = df['期缴保费'].min()
    max_ = df['期缴保费'].max()
    df['存量贡献率'] = df['期缴保费'].apply(lambda x: cal_increase_contribution(x, mean, min_, max_))
    return df
