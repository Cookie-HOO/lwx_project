import xlwings as xw


def call_excel_macro(excel_path, macro_names, run_mute):
    # 打开Excel
    app = xw.App(visible=not run_mute, add_book=False)
    # 打开含有宏的工作簿
    workbook = app.books.open(excel_path)
    # 运行宏
    for macro_name in macro_names:
        app.api.Application.Run(macro_name)
    # 关闭工作簿
    workbook.save()
    workbook.close()
    # 关闭Excel
    app.quit()
