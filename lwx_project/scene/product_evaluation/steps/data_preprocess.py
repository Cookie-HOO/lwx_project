def main(df_detail, df_abbr):
    """
    :param df_detail:
        分行代理保险产品分险种销售情况统计表.xlsx
    :param df_abbr:  COMPANY_ABBR_PATH
        对应表.xlsx
    :return:
    """
    # df = pd.read_excel(PRODUCT_DETAIL_PATH)
    # 脏数据处理：删除行列
    df_detail.drop(
        index=df_detail[(df_detail["保险公司"].str.contains('财产')) | (df_detail['保险公司'] == '利宝保险有限公司') | df_detail['本期实现保费'].isna()].index,
        columns=['公司代码'],
        inplace=True
    )

    # 处理公司名称
    df_detail["保险公司"] = df_detail["保险公司"].apply(lambda x: x.replace(' ', ''))

    # 匹配简称
    # df_product_list = pd.read_excel(COMPANY_ABBR_PATH)
    df_abbr["全称"] = df_abbr["全称"].apply(lambda x: x.replace(' ', ''))
    df = df_detail.merge(df_abbr, how='left', left_on='保险公司', right_on='全称')
    return df


if __name__ == '__main__':
    main()
