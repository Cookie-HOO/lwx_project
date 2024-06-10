import pandas as pd

from lwx_project.scene.product_evaluation.const import *


def main():
    df = pd.read_excel(PRODUCT_DETAIL_PATH)
    # 脏数据处理：删除行列
    df.drop(
        index=df[(df["保险公司"].str.contains('财产')) | (df['保险公司'] == '利宝保险有限公司') | df['本期实现保费'].isna()].index,
        columns=['公司代码'],
        inplace=True
    )

    # 处理公司名称
    df["保险公司"] = df["保险公司"].apply(lambda x: x.replace(' ', ''))

    # 匹配简称
    df_product_list = pd.read_excel(COMPANY_ABBR_PATH)
    df = df.merge(df_product_list, how='left', left_on='保险公司', right_on='全称')
    return df


if __name__ == '__main__':
    main()
