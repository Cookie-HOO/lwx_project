"""
同业交流ppt制作场景

初始化
1. 上传5个文件，必须时5个
    - 其中四个时工农中建四行，一个是上次做的结果
2. 复制上次的结果名字为这次的结果
    - 对号入座进行复制

操作：
1. 文字：将所有模板ppt中的文字改成当前日期
2. 图片：在excel中做好画图的内容，争取只做画图的截图然后搬运

下载做完的ppt
"""
from lwx_project.scene.monthly_communication_ppt.const import TMP_DUAN_BAR_PATH, TMP_DUAN_PIE_PATH, \
    TMP_YIWAI_BAR_PATH, TMP_JIANKANG_BAR_PATH, TMP_SHOU_BAR_PATH, TMP_RENJUN_BAR_PATH, PPT_TEMPLATE_PATH
from lwx_project.scene.monthly_communication_ppt.text_processor import find_max_and_up_or_down, make_tongbi_text
from lwx_project.scene.monthly_communication_ppt.utils import make_ppt_file_path, make_excel_file_path, make_month_range
from lwx_project.utils.excel_style import ExcelStyleValue
from lwx_project.utils.file import copy_file
from lwx_project.utils.high_performance import FastExcelReader
from lwx_project.utils.pptx_style import PPTXStyle
from lwx_project.utils.year_month_obj import YearMonth


def copy_4sheet_to_one_file(files, year_month_obj: YearMonth):
    """
    必须是5个文件，将上次做的结果复制一份到important目录，重命名为当前日期
    将剩下四个对号入座拷贝到这个文件的对应sheet

    将模板ppt文件拷贝一个出来
    """
    gong_path = ""
    nong_path = ""
    zhong_path = ""
    jian_path = ""
    target_path = ""
    for file in files:
        with FastExcelReader(file) as fer:
            if len(fer.sheets()) > 1:
                check, reason = fer.check_sheets(["工", "农", "中", "建", "工同比", "农同比", "中同比", "建同比"])
                if not check:
                    return False, f"上期结果缺少关键sheet: {reason}"
                target_path = file
            else:
                v = fer.get_cell_value(row_num=2, col_num=4)
                if v.startswith("工"):
                    gong_path = file
                elif v.startswith("农"):
                    nong_path = file
                elif v.startswith("中"):
                    zhong_path = file
                elif v.startswith("建"):
                    jian_path = file
                else:
                    return False, f"上传了无法解析的文件: {file}"

    if not (gong_path and nong_path and zhong_path and jian_path and target_path):
        return False, "工农中建以及上期结果的5个文件必须有"

    # 处理结果文件
    esv = ExcelStyleValue(target_path, run_mute=True)
    esv.batch_rename_sheet({
        "工同比": "工1",
        "农同比": "农1",
        "中同比": "中1",
        "建同比": "建1",
    })
    esv.batch_rename_sheet({
        "工": "工同比",
        "农": "农同比",
        "中": "中同比",
        "建": "建同比",
    })
    esv.batch_rename_sheet({
        "工1": "工",
        "农1": "农",
        "中1": "中",
        "建1": "建",
    })
    esv.switch_sheet("工")
    esv.copy_sheet_from_other_excel(gong_path)
    esv.switch_sheet("农")
    esv.copy_sheet_from_other_excel(nong_path)
    esv.switch_sheet("中")
    esv.copy_sheet_from_other_excel(zhong_path)
    esv.switch_sheet("建")
    esv.copy_sheet_from_other_excel(jian_path)

    # excel修改和保存图片
    esv.switch_sheet("短险保费同比增长").set_cell("B1", f"{year_month_obj.year-1}年").set_cell("C1", f"{year_month_obj.year}年")
    pics = esv.get_pictures()
    for p in pics:
        print(p)
    esv.save_pic(1, TMP_DUAN_BAR_PATH)  # 柱图
    esv.save_pic(2, TMP_DUAN_PIE_PATH)  # 饼图

    esv.switch_sheet("意外险").save_pic(0, TMP_YIWAI_BAR_PATH)
    esv.switch_sheet("健康险").save_pic(0, TMP_JIANKANG_BAR_PATH)
    esv.switch_sheet("寿险").save_pic(0, TMP_SHOU_BAR_PATH)
    esv.switch_sheet("人均产能（短险）").save_pic(0, TMP_RENJUN_BAR_PATH)

    esv.save(make_excel_file_path(year_month_obj))
    return True, ""

def makeup_date_text_in_ppt(year_month_obj: YearMonth):
    """
    找到构造ppt的目录，然后找到里面所有跟日期相关的文字进行修改
    """
    # 复制文件
    copy_file(PPT_TEMPLATE_PATH, make_ppt_file_path(year_month_obj=year_month_obj))
    year_str = str(year_month_obj.year)
    month_str = str(year_month_obj.month)
    month_range = make_month_range(year_month_obj)
    # 1. 第一页的标题
    ppt_stype = PPTXStyle(pptx_file_path=make_ppt_file_path(year_month_obj=year_month_obj))
    ppt_stype.replace_text(
        slide_index=0,
        old_text_pattern=".*?银行系寿险公司2025年1-8月团险经营情况.*?",
        new_text_parts=["银行系寿险", "公司", year_str, "年", month_range, "月团", "险经营情况"]
    ).replace_text(
        slide_index=0,
        old_text_pattern=".*?2025年9月.*?",
        new_text_parts=[year_str, "年", month_str, "月"],
    )

    # 2. 第二页的处理
    ppt_stype.replace_text(
        slide_index=1,
        old_text_pattern=f"各公司{year_str}年{month_str}月当月团险保费情况",
        new_text_parts=["各","公司",year_str,"年",month_str,"月","当月团险","保费情况" ]
    )
    # 3. 第三页的处理
    ppt_stype.replace_text(
        slide_index=2,
        old_text_pattern=f"各公司{year_str}年累计团险保费情况",
        new_text_parts=["各","公司",year_str,"年累计","团险","保费情况"]
    )
    # 4. 第四页
    ppt_stype.replace_text(
        slide_index=3,
        old_text_pattern=f"团险短险业务同比增长情况{month_range}",
        new_text_parts=["团险短险","业务","同比增长情况（",month_range,"月）" ]
    )
    # 5. 第五页
    ppt_stype.replace_text(
        slide_index=4,
        old_text_pattern=f"团险短险业务市场份额情况{month_range}",
        new_text_parts=["团险短险","业务市场份额","情况（",month_range,"月）" ]
    )
    # 6. 第六页
    ppt_stype.replace_text(
        slide_index=5,
        old_text_pattern=f"短险保费情况——意外险{month_range}",
        new_text_parts=["短","险","保费情况","——","意外险（",month_range,"月）" ]
    )
    # 7. 第七页
    ppt_stype.replace_text(
        slide_index=6,
        old_text_pattern=f"短险保费情况——健康险{month_range}",
        new_text_parts=["短","险","保费情况","——","健康","险（",month_range,"月）" ]
    )
    # 8. 第八页
    ppt_stype.replace_text(
        slide_index=7,
        old_text_pattern=f"短险保费情况——寿险{month_range}",
        new_text_parts=["短","险","保费情况","——","寿险（",month_range,"月）" ]
    )
    # 9. 第九页
    ppt_stype.replace_text(
        slide_index=8,
        old_text_pattern=f"短险人均产能情况{month_range}",
        new_text_parts=["短险","人均","产能","情况（",month_range,"月）" ]
    )

    ppt_stype.save(make_ppt_file_path(year_month_obj))

    pass

def makeup_pic_and_text_in_ppt(year_month_obj: YearMonth):
    """
    找到构造ppt的目录，将做好的图片放到对应位置，根据数字修改对应地方的文字
    """
    targe_excel_path = make_excel_file_path(year_month_obj=year_month_obj)

    ppt_style = PPTXStyle(pptx_file_path=make_ppt_file_path(year_month_obj=year_month_obj))
    esv = ExcelStyleValue(make_excel_file_path(year_month_obj), run_mute=True)
    # 第二页：当月
    ppt_style.replace_table(
        slide_index=1,
        old_table_id=6,
        new_table_excel=targe_excel_path,
        new_table_sheet_id="当月表格",
        new_table_value_range="A3:H8"
    )
    # 第三页：累计
    ppt_style.replace_table(
        slide_index=2,
        old_table_id=4,
        new_table_excel=targe_excel_path,
        new_table_sheet_id="当月表格",
        new_table_value_range="A12:H17"
    )
    # 第四页：短险增长
    esv.switch_sheet("短险保费同比增长")
    max_bank, max_amount, max_tongbi, tongbi_up_list, tongbi_down_list = find_max_and_up_or_down(
        bank2amount={"工银安盛": esv.get_cell("C2"), "农银人寿": esv.get_cell("C3"), "中银三星": esv.get_cell("C4"), "建信人寿": esv.get_cell("C5")},
        bank2tongbi={"工银安盛": esv.get_cell("D2"), "农银人寿": esv.get_cell("D3"), "中银三星": esv.get_cell("D4"), "建信人寿": esv.get_cell("D5")},
    )
    tongbi_text = make_tongbi_text(tongbi_up_list, tongbi_down_list, "短险业务")
    ppt_style.replace_pic(
        slide_index=3,
        old_pic_id=7,
        new_pic_path=TMP_DUAN_BAR_PATH,
    )
    ppt_style.replace_text(
        slide_index=3,
        old_text_pattern="建.*?",
        new_text_parts=[f"{max_bank}短险保费规模最大，同比","上升" if max_tongbi > 0 else "下降", str(max_tongbi * 100),"%","。" ],  # ["建信人寿短险保费规模最大，同比","上升","11.08","%","。" ]
    )
    ppt_style.replace_text(
        slide_index=3,
        old_text_pattern="四家银行系子公司短险业务同比均上升",
        new_text_parts=[tongbi_text, ""],  # ["四家银行系子公司短险业务同比","均上升。" ]
    )
    # 第五页：短险市场
    max_bank, max_amount, max_tongbi, tongbi_up_list, tongbi_down_list = find_max_and_up_or_down(
        bank2amount={"工银安盛": esv.get_cell("F2"), "农银人寿": esv.get_cell("F3"), "中银三星": esv.get_cell("F4"), "建信人寿": esv.get_cell("F5")},
        bank2tongbi={"工银安盛": esv.get_cell("G2"), "农银人寿": esv.get_cell("G3"), "中银三星": esv.get_cell("G4"), "建信人寿": esv.get_cell("G5")},
    )
    tongbi_text = make_tongbi_text(tongbi_up_list, tongbi_down_list, "短险业务份额")

    ppt_style.replace_pic(
        slide_index=4,
        old_pic_id=5,
        new_pic_path=TMP_DUAN_PIE_PATH,
    )
    ppt_style.replace_text(
        slide_index=4,
        old_text_pattern="建.*?",
        new_text_parts=[f"{max_bank}短险业务市场份额最大，占比",str(max_amount*100),"%","。" ],  # ["建信人寿短险业务市场份额最大，占比","49.1","%","。" ]
    )
    ppt_style.replace_text(
        slide_index=4,
        old_text_pattern="农银人寿、中银三星、建信人寿短险业务份额同比上升；工银安盛同比下降。",
        new_text_parts=[tongbi_text, "", ""],  # ["农银人寿、中银三星","、建信人寿","短险业务份额同比上升；工银安盛同比下降。" ]
    )
    # 第六页：意外险
    esv.switch_sheet("意外险")
    max_bank, max_amount, max_tongbi, tongbi_up_list, tongbi_down_list = find_max_and_up_or_down(
        bank2amount={"工银安盛": esv.get_cell("C2"), "农银人寿": esv.get_cell("C3"), "中银三星": esv.get_cell("C4"), "建信人寿": esv.get_cell("C5")},
        bank2tongbi={"工银安盛": esv.get_cell("D2"), "农银人寿": esv.get_cell("D3"), "中银三星": esv.get_cell("D4"), "建信人寿": esv.get_cell("D5")},
    )
    tongbi_text = make_tongbi_text(tongbi_up_list, tongbi_down_list, "意外险保费规模")

    ppt_style.replace_pic(
        slide_index=5,
        old_pic_id=7,
        new_pic_path=TMP_YIWAI_BAR_PATH,
    )
    ppt_style.replace_text(
        slide_index=5,
        old_text_pattern="保费规模.*?",
        new_text_parts=["保费规模：",max_bank,"意外险保费规","模排名第一。" ],  # ["保费规模：","建信人寿","意外险保费规","模排名第一。" ]
    )
    ppt_style.replace_text(
        slide_index=5,
        old_text_pattern="同比情况.*?",
        new_text_parts=["同比情况：",tongbi_text,"","","",""],  # ["同比情况：","中银三星、","建信人寿","意外险保费规模同比上升；工银安盛、","农银人寿","同比下降。" ]
    )
    # 第七页：健康险
    # 
    esv.switch_sheet("健康险")
    max_bank, max_amount, max_tongbi, tongbi_up_list, tongbi_down_list = find_max_and_up_or_down(
        bank2amount={"工银安盛": esv.get_cell("C2"), "农银人寿": esv.get_cell("C3"), "中银三星": esv.get_cell("C4"), "建信人寿": esv.get_cell("C5")},
        bank2tongbi={"工银安盛": esv.get_cell("D2"), "农银人寿": esv.get_cell("D3"), "中银三星": esv.get_cell("D4"), "建信人寿": esv.get_cell("D5")},
    )
    tongbi_text = make_tongbi_text(tongbi_up_list, tongbi_down_list, "健康险保费规模")

    ppt_style.replace_pic(
        slide_index=6,
        old_pic_id=2,
        new_pic_path=TMP_JIANKANG_BAR_PATH,
    )
    ppt_style.replace_text(
        slide_index=6,
        old_text_pattern="保费规模.*?",
        new_text_parts=["保费规模：",max_bank,"健康险保费规模排名第一，同比","上升" if max_tongbi>0 else "下降", str(max_tongbi*100),"%","。" ],  # ["保费规模：","建信人寿","健康险保费规模排名第一，同比","上升","10.97","%","。" ]
    )
    ppt_style.replace_text(
        slide_index=6,
        old_text_pattern="同比情况.*?",
        new_text_parts=[["同比情况：",tongbi_text,"" ]],  # ["同比情况：","四家银行系子公司健康险保费规模同比","均上升。" ]
    )
    # 第七页：寿险
    esv.switch_sheet("寿险")
    max_bank, max_amount, max_tongbi, tongbi_up_list, tongbi_down_list = find_max_and_up_or_down(
        bank2amount={"工银安盛": esv.get_cell("C2"), "农银人寿": esv.get_cell("C3"), "中银三星": esv.get_cell("C4"), "建信人寿": esv.get_cell("C5")},
        bank2tongbi={"工银安盛": esv.get_cell("D2"), "农银人寿": esv.get_cell("D3"), "中银三星": esv.get_cell("D4"), "建信人寿": esv.get_cell("D5")},
    )
    tongbi_text = make_tongbi_text(tongbi_up_list, tongbi_down_list, "寿险保费规模")

    ppt_style.replace_pic(
        slide_index=7,
        old_pic_id=2,
        new_pic_path=TMP_SHOU_BAR_PATH,
    )
    ppt_style.replace_text(
        slide_index=7,
        old_text_pattern="保费规模.*?",
        new_text_parts=["保费规模：",f"寿险规模{max_bank}排名第一，同比" + "上升" if max_tongbi > 0 else "下降",str(max_tongbi*100),"%","。" ],  # ["保费规模：","寿险规模工银安盛排名第一，同比下降","3.16","%","。" ]
    )
    ppt_style.replace_text(
        slide_index=7,
        old_text_pattern="同比情况.*?",
        new_text_parts=["同比情况：",tongbi_text, "","","","" ],  # ["同比情况：","农银人寿寿险保费规模同比上升，","工银安盛、","中银三星、","建信人寿同比下降","。" ]
    )
    # 第八页：人均
    esv.switch_sheet("人均产能（短险）")
    max_bank, max_amount, max_tongbi, tongbi_up_list, tongbi_down_list = find_max_and_up_or_down(
        bank2amount={"工银安盛": esv.get_cell("D2"), "农银人寿": esv.get_cell("D3"), "中银三星": esv.get_cell("D4"), "建信人寿": esv.get_cell("D5")},
        bank2tongbi={"工银安盛": esv.get_cell("D2"), "农银人寿": esv.get_cell("D3"), "中银三星": esv.get_cell("D4"), "建信人寿": esv.get_cell("D5")},
    )
    ppt_style.replace_pic(
        slide_index=8,
        old_pic_id=2,
        new_pic_path=TMP_RENJUN_BAR_PATH,
    )
    ppt_style.replace_text(
        slide_index=8,
        old_text_pattern="人.*?最高",
        new_text_parts=["人均产能：",max_bank,"最高。" ],  # ["人均产能：","工银安盛","最高。" ]
    )
    # ppt_style.replace_text(
    #     slide_index=8,
    #     old_text_pattern="注.*?",
    #     new_text_parts=[],  # ["注：产","能按短","险","保费统计，不含","长险、医疗","基金。" ]
    # )
    esv.discard()
    ppt_style.save()

    pass


if __name__ == '__main__':
    import os
    from lwx_project.scene.monthly_communication_ppt.const import IMPORTANT_PATH
    year_month_obj =  YearMonth(year=2025, month=10)
    r = copy_4sheet_to_one_file(files=[
        os.path.join(IMPORTANT_PATH, "工.xlsx"),
        os.path.join(IMPORTANT_PATH, "PPT数据-202508（公式版）.xlsx"),
        os.path.join(IMPORTANT_PATH, "农.xlsx"),
        os.path.join(IMPORTANT_PATH, "中.xlsx"),
        os.path.join(IMPORTANT_PATH, "建.xlsx"),
    ], year_month_obj = year_month_obj)
    makeup_date_text_in_ppt(year_month_obj=year_month_obj)

    makeup_pic_and_text_in_ppt(year_month_obj)