import os

from lwx_project.scene.comprehensive.const import DATA_TMP_PATH

SCORE_PATH = os.path.join(DATA_TMP_PATH, "分公司综合管理评价指标统计-计算版.xlsx")

# TEMPLATE
TITLE_TEMPLATE = "{year_num}年{month_num}月分公司团险部综合管理评价得分"
EXTRA_TEMPLATE1 = """注：
1.数据为截至{month_num}月底数据，分公司分管总及团险部经理以{last_day_of_month}实际在岗为准。
"""
EXTRA_TEMPLATE2 = "2.标红项为超过平均值数据。"

