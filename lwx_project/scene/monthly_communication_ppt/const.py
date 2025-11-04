import os

from lwx_project.const import ALL_DATA_PATH, STATIC_PATH

DATA_PATH = os.path.join(ALL_DATA_PATH, "monthly_communication_ppt")
IMPORTANT_PATH = os.path.join(DATA_PATH, "important")

PPT_TEMPLATE_PATH = os.path.join(IMPORTANT_PATH, "模板.pptx")
PPT_FILE_NAME_TEMPLATE = "银行系寿险公司{year}年{month_range}月团险经营情况.pptx"  # 银行系寿险公司2025年1-8月团险经营情况.pptx
EXCEL_FILE_NAME_TEMPLATE = "银行系寿险公司{year}年{month_range}月团险经营情况.xlsx"  # 银行系寿险公司2025年1-8月团险经营情况.xlsx

TMP_DUAN_BAR_PATH = os.path.join(IMPORTANT_PATH, "tmp_duan_bar.png")  # 短
TMP_DUAN_PIE_PATH = os.path.join(IMPORTANT_PATH, "tmp_duan_pie.png")  # 短

TMP_YIWAI_BAR_PATH = os.path.join(IMPORTANT_PATH, "tmp_yiwai_bar.png")  # 意外
TMP_JIANKANG_BAR_PATH = os.path.join(IMPORTANT_PATH, "tmp_jiankang_bar.png")  # 健康
TMP_SHOU_BAR_PATH = os.path.join(IMPORTANT_PATH, "tmp_shou_bar.png")  # 寿险
TMP_RENJUN_BAR_PATH = os.path.join(IMPORTANT_PATH, "tmp_renjun_bar.png")  # 人均

SCENE_IMPORTANT_PIC_PATH = os.path.join(STATIC_PATH, "scene_important_pic", "monthly_communication_ppt")
