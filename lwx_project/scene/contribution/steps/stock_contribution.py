def main(df):
    df['存量贡献率'] = (df['期缴保费'] - df['期缴保费'].min()) / (df['期缴保费'].max() - df['期缴保费'].min())
    return df
