import typing

from lwx_project.utils.excel_macro import call_excel_macro
from lwx_project.utils.file import get_file_name_with_extension
from lwx_project.utils.high_performance import FastExcelReader
from lwx_project.utils.year_month_obj import YearMonth

"""
业务工具函数，和具体业务强相关，跨业务场景的工具函数放在这里
"""

def core_tuanxian_get_month(detail_path: str) -> typing.Optional[YearMonth]:
    """核心团险表：经常需要读取，写一个专门的工具函数来处理 日期问题
    高效读取 Excel 文件前两行：
    - 第一行：列名，查找「日期」列
    - 找到日期列对应的第二行数据，提取日期值
    返回 datetime.date 对象。
    """
    with FastExcelReader(detail_path) as fe:
        col_num = fe.posit_col_in_row_by_value(row_num=1, value="日期")
        date_value = fe.get_cell_value(2, col_num)
        if date_value:
            return YearMonth.new_from_str(date_value)

    return None


def sheet_capture(excel_path, sheet_name_or_index, img_path, padding=None, run_mute=False):
    """将生成的excel的sheet进行截图
    excel_path: 哪个excel，必须xlsm结尾
    sheet_name_or_index: sheet名称或index
    img_path: 存到哪里
    padding: 截图的四周白色边：up right bottom left
    run_mute: 是否静默执行
    :return:

    截图的宏：需要提前写在xlsm中，代码中给出示例
    目标机器只有wps则无法动态插入宏，如果有excel，可以动态插入宏
    """

    # 截图的宏：需要提前写在xlsm中：
    # 第一个参数是图片地址（.png），第二个参数是sheet的name或者index
    """
    Sub 生成图片(imgPath As String, sheetIdentifier As Variant, Optional topPadding As Integer = 0, Optional rightPadding As Integer = 0, Optional bottomPadding As Integer = 0, Optional leftPadding As Integer = 0)
        Dim ws As Worksheet
        Dim chartObj As ChartObject

        ' 设置图片保存路径
        ' imgPath = "D:\projects\lwx_project\SheetImage2.png" ' 修改为你想要保存的路径

        ' 设置要转换的工作表
        ' Set ws = ActiveSheet ' 或者使用 Sheets("SheetName") 来指定特定的工作表
       ' 根据传入的参数类型选择工作表
        Set ws = Sheets(sheetIdentifier)

        ' 关闭网格线显示
        ws.Activate
        ActiveWindow.DisplayGridlines = False
        ' ws.Application.Windows(ws.Parent.Name).DisplayGridlines = False   这种写法不起作用
        ' 将工作表的内容复制为图片
        ws.UsedRange.CopyPicture Appearance:=xlScreen, Format:=xlBitmap


        ' 创建一个足够大的图表对象来容纳整个UsedRange
        Set chartObj = ws.ChartObjects.Add(Left:=0, Top:=0, Width:=ws.UsedRange.Width + leftPadding + rightPadding, Height:=ws.UsedRange.Height + topPadding + bottomPadding)
        With chartObj
            ' 确保图表没有边框和白边
            .Chart.ChartArea.Border.LineStyle = xlLineStyleNone
            .Chart.ChartArea.Format.Fill.Visible = msoTrue
             .Chart.ChartArea.Format.Fill.ForeColor.RGB = RGB(255, 255, 255) ' 设置背景色为白色
            .Chart.PlotArea.Border.LineStyle = xlLineStyleNone
            .Chart.PlotArea.Format.Fill.Visible = msoFalse
            ' 粘贴图片到图表区域
            .Chart.Paste
            ' 调整图表区域大小以匹配图片大小
            .Width = .Chart.ChartArea.Width
            .Height = .Chart.ChartArea.Height
             ' 将图片移动到图表的中心位置
            .Chart.Pictures(1).Top = topPadding
            .Chart.Pictures(1).Left = leftPadding
        End With

        ' 导出图表为图片
        chartObj.Chart.Export Filename:=imgPath, FilterName:="PNG"

        ' 删除临时创建的图表对象
        chartObj.Delete

        ' 恢复网格线显示
        ActiveWindow.DisplayGridlines = True
        ' ws.Application.Windows(ws.Parent.Name).DisplayGridlines = True   这种写法不起作用
    End Sub

    """

    MACRO_NAME = "生成图片"  # 需要提前在excel中写入 宏，可参考
    padding = padding or [0, 0, 0, 0]
    file_name = get_file_name_with_extension(excel_path)
    macro_with_args = {
        f"{file_name}!{MACRO_NAME}": [img_path, sheet_name_or_index, *padding]
    }

    call_excel_macro(excel_path, marco_names_with_args=macro_with_args, run_mute=run_mute)

