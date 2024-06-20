from lwx_project.scene.daily_report.const import DAILY_REPORT_SOURCE_TEMPLATE_PATH, EXCEL_PIC_MARCO
from lwx_project.utils.excel import call_excel_macro


def main(excel_path, img_path, sheet_name_or_index, run_mute=False):
    """将生成的excel的sheet进行截图
    :return:
    """
    macro_with_args = {
        EXCEL_PIC_MARCO: [img_path, sheet_name_or_index]
    }

    call_excel_macro(excel_path, marco_names_with_args=macro_with_args, run_mute=run_mute)


if __name__ == '__main__':
    excel = DAILY_REPORT_SOURCE_TEMPLATE_PATH
    path = "D:\projects\lwx_project\l3.png"
    sheet = 4
    main(excel, path, sheet)