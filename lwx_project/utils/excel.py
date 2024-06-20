import xlwings as xw


def call_excel_macro(excel_path, macro_names=None, marco_names_with_args=None, run_mute=False):
    """
    :param excel_path:
    :param macro_names:
        [macro_name1, macro_name2, macro_name3]  直接调用
    :param marco_names_with_args:
        {"marco_nam1": []}  将value作为参数
    :param run_mute:
    :return:
    """
    # 打开Excel
    app = xw.App(visible=not run_mute, add_book=False)
    # 打开含有宏的工作簿
    workbook = app.books.open(excel_path)
    # 运行宏
    if macro_names:
        for macro_name in macro_names:
            app.api.Application.Run(macro_name)
    if marco_names_with_args:
        if isinstance(marco_names_with_args, dict):
            for macro_name, args in marco_names_with_args.items():
                if args:
                    app.api.Application.Run(macro_name, *args)
                else:
                    app.api.Application.Run(macro_name)
    # 关闭工作簿
    workbook.save()
    workbook.close()
    # 关闭Excel
    app.quit()
