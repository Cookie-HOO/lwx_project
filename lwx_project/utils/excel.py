import platform

call_excel_macro = None
if platform.system() == 'Windows':
    import win32com.client as wc
    def call_excel_macro_win(excel_path, macro_name):
        xlApp = wc.DispatchEx("Excel.Application")
        xlApp.Visible = True
        xlApp.DisplayAlerts = 0
        xlBook = xlApp.Workbooks.Open(excel_path)
        xlBook.Application.Run(macro_name)  # 宏
        xlBook.Close(True)


    call_excel_macro = call_excel_macro_win
elif platform.system() == 'Darwin':
    import xlwings as xw
    def call_excel_macro_mac(excel_path, macro_name):
        wb = xw.Book(excel_path)
        wb.macro(macro_name)()
        # app = wb.app
        # app.api.Application.Run(macro_name)
        wb.close()


    call_excel_macro = call_excel_macro_mac





