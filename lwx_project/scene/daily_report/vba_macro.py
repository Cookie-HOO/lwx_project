# 宏的具体内容
# 第一个宏：粘贴
__MACRO_1 = """
Sub 粘贴()
Dim 每日报表汇总 As Workbook
Dim 代理期缴保费 As Workbook

Set 代理期缴保费 = Workbooks.Open(ThisWorkbook.Path & "\代理期缴保费.xlsm")

Set 当年农 = Workbooks.Open(ThisWorkbook.Path & "\当年农.xlsx")
Application.CalculateFull '重新计算公式
当年农.Worksheets(1).Cells.Copy Workbooks("每日报表汇总.xlsm").Worksheets("当年农").Range("a1")
当年农.Close savechanges:=False

Set 当季农 = Workbooks.Open(ThisWorkbook.Path & "\当季农.xlsx")
Application.CalculateFull '重新计算公式
当季农.Worksheets(1).Cells.Copy Workbooks("每日报表汇总.xlsm").Worksheets("当季农").Range("a1")
当季农.Close savechanges:=False

Set 当月农 = Workbooks.Open(ThisWorkbook.Path & "\当月农.xlsx")
Application.CalculateFull '重新计算公式
当月农.Worksheets(1).Cells.Copy Workbooks("每日报表汇总.xlsm").Worksheets("当月农").Range("a1")
当月农.Close savechanges:=False

Set 当日农 = Workbooks.Open(ThisWorkbook.Path & "\当日农.xlsx")
Application.CalculateFull '重新计算公式
当日农.Worksheets(1).Cells.Copy Workbooks("每日报表汇总.xlsm").Worksheets("当日农").Range("a1")
当日农.Close savechanges:=False

Set 当年全 = Workbooks.Open(ThisWorkbook.Path & "\当年全.xlsx")
Application.CalculateFull '重新计算公式
当年全.Worksheets(1).Cells.Copy Workbooks("每日报表汇总.xlsm").Worksheets("当年全").Range("a1")
当年全.Worksheets(1).Cells.Copy Workbooks("代理期缴保费.xlsm").Worksheets("当年全").Range("a1")
当年全.Close savechanges:=False

Set 当日全 = Workbooks.Open(ThisWorkbook.Path & "\当日全.xlsx")
Application.CalculateFull '重新计算公式
当日全.Worksheets(1).Cells.Copy Workbooks("每日报表汇总.xlsm").Worksheets("当日全").Range("a1")
当日全.Worksheets(1).Cells.Copy Workbooks("代理期缴保费.xlsm").Worksheets("当日全").Range("a1")
当日全.Close savechanges:=False

Set 当日全统计 = Workbooks.Open(ThisWorkbook.Path & "\26当日全.xlsx")
Application.CalculateFull '重新计算公式
当日全统计.Worksheets(1).Cells.Copy Workbooks("每日报表汇总.xlsm").Worksheets("26当日全").Range("a1")
当日全统计.Close savechanges:=False

Set 当年全统计 = Workbooks.Open(ThisWorkbook.Path & "\26当年全.xlsx")
Application.CalculateFull '重新计算公式
当年全统计.Worksheets(1).Cells.Copy Workbooks("每日报表汇总.xlsm").Worksheets("26当年全").Range("a1")
当年全统计.Close savechanges:=False

Set 当日公司 = Workbooks.Open(ThisWorkbook.Path & "\当日公司.xlsx")
Application.CalculateFull '重新计算公式
当日公司.Worksheets(1).Cells.Copy Workbooks("每日报表汇总.xlsm").Worksheets("当日公司").Range("a1")
当日公司.Close savechanges:=False

Set 当年公司 = Workbooks.Open(ThisWorkbook.Path & "\当年公司.xlsx")
Application.CalculateFull '重新计算公式
当年公司.Worksheets(1).Cells.Copy Workbooks("每日报表汇总.xlsm").Worksheets("当年公司").Range("a1")
当年公司.Close savechanges:=False

Set 网点表 = Workbooks.Open(ThisWorkbook.Path & "\公司网点经营情况统计表.xlsx")
Application.CalculateFull '重新计算公式
网点表.Worksheets(1).Cells.Copy Workbooks("每日报表汇总.xlsm").Worksheets("网点表").Range("a1")
网点表.Close savechanges:=False

Set 农行渠道实时业绩报表 = Workbooks.Open(ThisWorkbook.Path & "\农行渠道实时业绩报表.xlsx")
农行渠道实时业绩报表.Worksheets(1).Cells.Copy Workbooks("每日报表汇总.xlsm").Worksheets("农行渠道实时业绩报表").Range("a1")
农行渠道实时业绩报表.Close savechanges:=False

Workbooks("每日报表汇总.xlsm").Worksheets("农行渠道实时业绩报表").Columns("m").Insert Shift:=xlToRight, Copyorigin:=xlFormatFromLeftOrAbove

代理期缴保费.Save
代理期缴保费.Close

Set 当日活动率 = Workbooks.Open(ThisWorkbook.Path & "\23当日活动率.xlsx")
Application.CalculateFull '重新计算公式
当日活动率.Worksheets(1).Cells.Copy Workbooks("每日报表汇总.xlsm").Worksheets("23当日活动率").Range("a1")
当日活动率.Close savechanges:=False

Set 当月活动率 = Workbooks.Open(ThisWorkbook.Path & "\23当月活动率.xlsx")
Application.CalculateFull '重新计算公式
当月活动率.Worksheets(1).Cells.Copy Workbooks("每日报表汇总.xlsm").Worksheets("23当月活动率").Range("a1")
当月活动率.Close savechanges:=False

Set 农银日平台 = Workbooks.Open(ThisWorkbook.Path & "\业绩报表.xlsx")
Application.CalculateFull '重新计算公式
农银日平台.Worksheets(1).Cells.Copy Workbooks("每日报表汇总.xlsm").Worksheets("农银日平台").Range("a1")
农银日平台.Close savechanges:=False

End Sub
"""

# 第二个宏：排序
__MACRO_2 = """
Sub 补充()
Dim lastrow As Long
Dim rng As Range
Dim cell As Range

Sheets("农行渠道实时业绩报表").Select
For i = 7 To 29
Range("m" & i).Value = Left(Range("c" & i).Value, 2)
Next i

Worksheets("农行渠道实时业绩报表").Cells.Copy Worksheets("农银实时").Range("a1")
Sheets("文字").Select

With ThisWorkbook.Sheets("报表1农银日报")
.Range("A5:O26").Sort Key1:=.Range("G5:G26"), Order1:=xlDescending, Header:=xlNo

End With

With ThisWorkbook.Sheets("报表2-季度保费完成率")
.Range("A5:J26").Sort Key1:=.Range("I5:I26"), Order1:=xlDescending, Header:=xlNo

End With

With ThisWorkbook.Sheets("报表3-月保费情况")
.Range("A4:J25").Sort Key1:=.Range("J4:J25"), Order1:=xlDescending, Header:=xlNo

End With

With ThisWorkbook.Sheets("报表4-网点活动率情况")
.Range("A5:E26").Sort Key1:=.Range("E5:E26"), Order1:=xlDescending, Header:=xlNo

End With

With ThisWorkbook.Sheets("四季度达成率")
.Range("A4:F25").Sort Key1:=.Range("F4:F25"), Order1:=xlDescending, Header:=xlNo

End With

With ThisWorkbook.Sheets("犹豫期撤单")
.Range("A2:D23").Sort Key1:=.Range("C2:C23"), Order1:=xlDescending, Header:=xlNo

End With

With ThisWorkbook.Sheets("日平台目标")
.Range("A5:N26").Sort Key1:=.Range("E5:E26"), Order1:=xlDescending, Header:=xlNo

End With

With ThisWorkbook.Sheets("周计划日平台")
.Range("A4:H25").Sort Key1:=.Range("G4:G25"), Order1:=xlDescending, Header:=xlNo

End With

With ThisWorkbook.Sheets("公司表")
.Range("A6:N60").Sort Key1:=.Range("I5:I60"), Order1:=xlDescending, Header:=xlNo

End With


With ThisWorkbook.Sheets("公司累计")
.Range("A6:Q60").Sort Key1:=.Range("I5:I60"), Order1:=xlDescending, Header:=xlNo

End With

With ThisWorkbook.Sheets("分行累计")
.Range("A6:Q42").Sort Key1:=.Range("I6:I42"), Order1:=xlDescending, Header:=xlNo

End With

With ThisWorkbook.Sheets("临时")
.Range("A5:F26").Sort Key1:=.Range("E5:E26"), Order1:=xlAscending, Header:=xlNo

End With

Set 网点表 = ThisWorkbook.Sheets("网点表")
lastrow = 网点表.Cells(网点表.Rows.Count, "E").End(xlUp).Row
Set rng = 网点表.Range("E1:E" & lastrow)
For Each cell In rng
    cell.Value = Val(cell.Value)
    Next cell
    rng.NumberFormat = "general"

With ThisWorkbook.Sheets("每日活动率")
.Range("A6:O42").Sort Key1:=.Range("K6:K42"), Order1:=xlDescending, Header:=xlNo

End With

ThisWorkbook.Save

End Sub
"""

# 第三个宏：生成图片：第一个参数是图片地址（.png），第二个参数是sheet的name或者index
__MACRO_3 = """
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