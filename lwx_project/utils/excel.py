import xlwings as xw
import win32com.client as wc


def call_excel_macro_by_xlwings(excel_path, macro_names=None, marco_names_with_args=None, run_mute=False):
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
    func = app.api.Application.Run
    __run_macro(func, macro_names=macro_names, marco_names_with_args=marco_names_with_args)

    # 关闭工作簿
    workbook.save()
    workbook.close()
    # 关闭Excel
    app.quit()


def call_excel_macro_by_win32(excel_path, macro_names=None, marco_names_with_args=None, run_mute=False):
    """
    :param excel_path:
    :param macro_names:
        [macro_name1, macro_name2, macro_name3]  直接调用
    :param marco_names_with_args:
        {"marco_nam1": []}  将value作为参数
    :param run_mute:
    :return:
    """

    xlApp = wc.DispatchEx("Excel.Application")
    xlApp.Visible = not run_mute
    xlApp.DisplayAlerts = 0
    xlBook = xlApp.Workbooks.Open(excel_path)
    func = xlBook.Application.Run
    __run_macro(func, macro_names=macro_names, marco_names_with_args=marco_names_with_args)
    xlBook.Close(True)


def call_excel_macro_by_xlwings2(excel_path, macro_names=None, marco_names_with_args=None, run_mute=False):
    """
    :param excel_path:
    :param macro_names:
        [macro_name1, macro_name2, macro_name3]  直接调用
    :param marco_names_with_args:
        {"marco_nam1": []}  将value作为参数
    :param run_mute:
    :return:
    """
    wb = xw.Book(excel_path)
    func = wb.macro
    macro_names = macro_names or []
    marco_names_with_args = marco_names_with_args or {}

    macro_names = [i.split("!")[-1] for i in macro_names]
    marco_names_with_args = {key.split("!")[-1]: value for key, value in marco_names_with_args.items()}
    __run_macro(func, macro_names=macro_names, marco_names_with_args=marco_names_with_args, currying=True)
    # app = wb.app
    # app.api.Application.Run(macro_name)
    wb.save()
    wb.close()


def __run_macro(func, macro_names=None, marco_names_with_args=None, currying=False):
    if macro_names:
        for macro_name in macro_names:
            if currying:
                func(macro_name)()
            else:
                func(macro_name)
    if marco_names_with_args:
        if isinstance(marco_names_with_args, dict):
            for macro_name, args in marco_names_with_args.items():
                if args:
                    if currying:
                        func(macro_name)(*args)
                    else:
                        func(macro_name, *args)
                else:
                    if currying:
                        func(macro_name)()
                    else:
                        func(macro_name)

call_excel_macro = call_excel_macro_by_xlwings

