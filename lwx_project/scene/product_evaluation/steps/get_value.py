import pandas as pd

from lwx_project.scene.product_evaluation.const import PRODUCT_LIST_PATH


def get_baoxian_type(df, all_baoxian_product):
    baoxian_name = df["险种名称"]
    baoxian_fee = df["保费"]
    if baoxian_name in all_baoxian_product:
        print(baoxian_name)
        return "团险"
    if baoxian_fee <= 0:
        return "无保费"
    return "有保费"


def main(df):
    df_for_value = df.drop(
        columns=["保险公司"]
    )
    df_for_value = df_for_value.rename(columns={
        "实际简称": "保险公司",
        "本期实现保费": "保费",
    })

    all_tuanxian_product_df = pd.read_excel(PRODUCT_LIST_PATH, sheet_name="团险", skiprows=1)
    all_tuanxian_product = all_tuanxian_product_df["产品名称"].dropna().values
    df_for_value["__保险类型"] = df_for_value.apply(lambda x: get_baoxian_type(x, all_tuanxian_product), axis=1)


    df_for_value["期数"] = ""
    yinbao_df = pd.read_excel(PRODUCT_LIST_PATH, sheet_name="银保", skiprows=1)
    sihang_df = pd.read_excel(PRODUCT_LIST_PATH, sheet_name="私行", skiprows=1)
    yinbao_and_sihang = pd.concat(
        [
            yinbao_df.dropna(subset=["产品名称"])[["产品名称", "期数"]],
            sihang_df.dropna(subset=["产品名称"])[["产品名称", "期数"]],
        ],
        axis=0

    )
    has_fee = df_for_value[df_for_value["__保险类型"] == '有保费']
    has_fee


    pass
