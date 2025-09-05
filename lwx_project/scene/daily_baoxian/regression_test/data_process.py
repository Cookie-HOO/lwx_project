from itertools import count

import pandas as pd

from lwx_project.scene.daily_baoxian.const import REGRESSION_PATH
from lwx_project.scene.daily_baoxian.vo import worker_manager

df = pd.read_csv(REGRESSION_PATH)
df = df.sort_values(by='原标题', ascending=False)

platform_1 = "中国招标投标公共服务平台"
platform_2 = "中国政府采购网"
counter = 0

total = len(df)



def pre_process_df():
    df["链接"] = df["招采平台"].apply(lambda x: "http" + x.split("http")[1].strip())

    df["招采平台"] = df["招采平台"].apply(lambda x: x.split("http")[0].strip().strip(":").strip("：").strip())
    df["获取招标文件的截止日期"] = df["获取招标文件的截止日期"].apply(lambda x: x.replace(r"\\n", "").strip())


def get_detail(row) -> (str, str):
    global counter
    counter += 1
    print(f"{counter}/{total}")
    title, detail = row["原标题"], row["详情信息"]
    platform = row["招采平台"]
    if not pd.isna(title) and not pd.isna(detail):
        return title, detail
    if platform not in [platform_1, platform_2]:
        return title, detail
    url = row["链接"]
    platform = row["招采平台"]
    title, detail = worker_manager.get_for_title_and_detail(platform, url)
    print(title)
    print(detail[:10] + "...")
    return title, detail

# pre_process_df()


# df = df.iloc[:1]


from lwx_project.scene.daily_baoxian.workers.gov_buy_worker import gov_buy_worker
from lwx_project.scene.daily_baoxian.workers.bid_info_worker import bid_info_worker

worker_manager.add_worker(bid_info_worker)
worker_manager.add_worker(gov_buy_worker)
worker_manager.init_browser("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
worker_manager.check_env()


results = []

for idx, row in df.iterrows():
    try:
        title, info = get_detail(row)
        results.append({
            '原标题_new': title,
            '详情信息_new': info,
            '索引': idx  # 可选：记录原始索引
        })
    except Exception as e:
        results.append({
            '原标题_new': "",
            '详情信息_new': str(e),
            '索引': idx  # 可选：记录原始索引
        })
        continue

# 将结果转换为 DataFrame
df_result = pd.DataFrame(results)

# 如果你想保留原始 DataFrame 中的其他列，可以合并回去
df_final = pd.merge(df, df_result, left_index=True, right_on='索引', how='left')


def merge_new_result(row):
    title, detail = row["原标题"], row["详情信息"]
    title_new, detail_new = row["原标题_new"], row["详情信息_new"]
    if pd.isna(title) or title == "":
        return pd.Series([title_new, detail_new])
    else:
        return pd.Series([title, detail])

df_final[["原标题_final", "详情信息_final"]] = df_final.apply(merge_new_result, axis=1)
# 步骤1: 删除原始的 A、B 列
df_final = df_final.drop(columns=['原标题', '详情信息', "原标题_new", "详情信息_new", "索引"])

# 步骤2: 将 A_、B_ 重命名为 A、B
df_final = df_final.rename(columns={'原标题_final': '原标题', '详情信息_final': '详情信息'})
# 保存成功的结果
df_final.to_csv('清洗结果.csv', index=False)


print("处理完成，结果已保存。")
