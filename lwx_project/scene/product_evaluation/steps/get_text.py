import pandas as pd

from lwx_project.scene.product_evaluation.const import *
from lwx_project.utils.calculator import num_or_na_or_zero
from lwx_project.utils.time_obj import TimeObj


def groupby_company(df_company):
    company_name = df_company["保险公司"].iloc[0]
    company_abbr = df_company["实际简称"].iloc[0]

    product_all_count = num_or_na_or_zero(df_company["公司小计"].iloc[0])
    product_type_list = [
        ("银保产品", num_or_na_or_zero(df_company["银保产品银保小计"].iloc[0])),
        ("私行产品", num_or_na_or_zero(df_company["私行产品私行小计"].iloc[0])),
        ("团险产品", num_or_na_or_zero(df_company["团险"].iloc[0])),
    ]
    product_type_count = [f"{value}款{name}" for name, value in product_type_list if value > 0]

    fee_total = df_company["本期实现保费"].sum() / 10000
    fee_way = df_company.groupby("缴费方式")["本期实现保费"].sum()
    qijiao_fee = fee_way.get("期缴", 0) / 10000
    dunjiao_fee = fee_way.get("趸缴", 0) / 10000
    main_product = df_company.groupby("险种名称")["本期实现保费"].sum().sort_values(ascending=False)

    main_product_top2 = [(
        name, value / 10000
    ) for name, value in zip(main_product.index[:2], main_product.values[:2])]
    main_product = [f"{name}：{'%.2f' % value}亿元" for name, value in main_product_top2 if value > 0]
    main_product_top2_fee = sum(i[1] for i in main_product_top2)

    today = TimeObj()
    text = TEXT_SUMMARY.format(
        until_last_season=today.until_last_season,
        company_name=company_name,
        company_abbr=company_abbr,
        product_all_count=product_all_count,
        # product_type_count: 5款银保产品，0款私行产品，0款团险产品
        product_type_count="，".join(product_type_count),
        fee_total='%.2f' % fee_total,
        # dun_qi_fee: ，其中趸缴{dunjiao_fee}亿元，期缴{qijiao_fee}亿元
        dun_qi_fee=f" ，其中趸缴{'%.2f' % dunjiao_fee}亿元，期缴{'%.2f' % qijiao_fee}亿元" if fee_total > 0 else '',
        # main_product: 人保寿险鑫安两全保险(分红型)(C款)：15.64亿元，人保寿险臻鑫一生终身寿险：2.9亿元
        main_product="，".join(main_product),
        main_product_fee_num='%.2f' % main_product_top2_fee,
        main_product_fee_percent='%.2f' % (main_product_top2_fee / fee_total * 100) + '%' if fee_total != 0 else "0",
    )
    return text


def main(df_detail, df_tongji):
    """
    :param df_detail: df_detail 和 abbr表合并后，带有简称的表
    :param df_tongji: 产品目录中的统计sheet，注意表头的合并
    :return:
    """
    df_for_text = df_detail[["保险公司", "实际简称", "险种名称", "缴费方式", "本期实现保费"]]
    # df_count = pd.read_excel(PRODUCT_LIST_PATH, sheet_name="统计")

    # 处理df_count表的表头问题
    # new_columns = df_count.iloc[0, :].ffill() + df_count.iloc[1, :].fillna(value='')
    # df_count.columns = new_columns
    # df_count.drop(index=[0, 1], inplace=True)
    df_tongji = df_tongji[["公司全称", "银保产品银保小计", "私行产品私行小计", "团险", "公司小计"]]

    df_merge = df_for_text.merge(df_tongji, how="left", left_on="保险公司", right_on="公司全称")

    return df_merge.groupby("实际简称", as_index=False).apply(groupby_company).rename(columns={None: "评价"})

