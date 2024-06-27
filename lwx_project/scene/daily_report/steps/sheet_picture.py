from lwx_project.scene.daily_report.const import DAILY_REPORT_SOURCE_TEMPLATE_PATH, EXCEL_PIC_MARCO
from lwx_project.utils.excel_macro import call_excel_macro


def main(excel_path, sheet_name_or_index, img_path, padding=None, run_mute=False):
    """将生成的excel的sheet进行截图
    excel_path: 哪个excel
    sheet_name_or_index: sheet名称或index
    img_path: 存到哪里
    padding: 截图的四周白色边：up right bottom left
    run_mute: 是否静默执行
    :return:
    """
    padding = padding or [0, 0, 0, 0]
    macro_with_args = {
        EXCEL_PIC_MARCO: [img_path, sheet_name_or_index, *padding]
    }

    call_excel_macro(excel_path, marco_names_with_args=macro_with_args, run_mute=run_mute)


if __name__ == '__main__':
    excel = DAILY_REPORT_SOURCE_TEMPLATE_PATH
    path = "D:\projects\lwx_project\l10.png"
    sheet = 11
    main(excel, path, sheet, run_mute=True)