"""
IMPORRTANT
    - 产品目录.xlsx
    - 分行代理保险产品分险种销售情况统计表.xlsx
    - 上期保费.xlsx
1. 预处理：
    文件：分行代理保险产品分险种销售情况统计表.xlsx
    1. 删除1列
        {公司代码}
    2. 删除行
        {保险公司}：包含 {财产} 的行
        OR
        {保险公司} == 利宝保险有限公司
    3. 匹配简称
        {产品目录.xlsx} 的 {对应表} 里面有简称
        匹配列：{产品目录.xlsx} 的 {对应表} 的 {全称}列   和     原文件的 {保险公司} 列
        新列叫：{实际简称}
    4. 处理公司
        {保险公司}列，去掉所有文字中的空格
    5. 处理备注
        删除{本期实现保费}列，为空的行

2. 得到2个总表
    总表2：目的是得到文字
        1. 列处理
            结果：保险公司	实际简称	险种名称	缴费方式	本期实现保费

    总表1：目的是得到数据
        0. 列处理
            1. 删除 {保险公司} 列
            2. 重命名
                将 {实际简称}列 重命名为 {保险公司}列
                将 {本期实现保费}列 重命名为 {保费}列
            3. 顺序调整
                结果：
                - before
                    保险公司	险种代码	险种名称	保险责任分类	保险责任子分类	缴费方式	保险期限	缴费期间	总笔数	保费	犹撤保费	退保保费	本期实现手续费收入
                - after
                    保险公司	险种名称	{期数}	保费	{其中：一、二季度保费}	险种代码	保险责任分类	保险责任子分类	保险期限	缴费期间	总笔数	犹撤保费	退保保费	本期实现手续费收入

                {期数}列：
                    有保费的后面会被填充
                    其他子表，这里保持空
                {其中：一、二季度保费}列
                    名字：看当前日期
                        处在一季度：没有这一列
                        处在二季度：{其中：一季度保费}
                        处在三季度：{其中：一、二季度保费}
                        处在四季度：{其中：一、二、三季度保费}
                    值：
                        在{上期保费.xlsx} 和 {总表1} 中 {险种名称}一样的列，对 {上期保费.xlsx} 中的 {本期实现保费} 求和
        1. 计算
            对{险种名称} groupby 求 {本期实现保费}的sum

        2. 得到3个表：三个加起来是全集
            团险表：
                条件：{险种名称} 出现在 {产品目录.xlsx}  的 {团险} sheet 的{产品名称}列 中
            无保费
                条件1：{本期实现保费} <= 0
                AND
                条件2：不是{团险}
            有保费
                条件1：不是{无保费}
                AND
                条件2：不是{团险}
        3. {有保费}的表匹配以得到{期数}
            {有保费}表的{产品名称}  匹配  {产品目录.xlsx}  的 {银保}和{私行} sheet的{产品名称}得到期数
            匹配规则
                严格匹配
                    1. 删除以下内容后完全一致，完全一致
                        删除中英文小括号
                        删除中英文逗号
                    2. 替换掉公司简称后，完全一致
                        两个字和四个字都可以
                    3. 可有可无：{保险产品}、{计划}、{年金}、{年金保险}、{分红}
                        可有可无的东西不能在小括号中，比如（分红型）不能删
                in匹配
                    1. 完全包含在 {产品目录.xlsx} 中，取期数最小的

                括号问题
                    华夏财富宝两全保险（分红型，鑫享版）          华夏财富宝两全保险（分红型）（鑫享版）

            如果处理完成全部可匹配，自动往下走，否则停止

        4.

3. 步骤1
    对 {有保费}的表 进行处理
    参考 tmp步骤一结果.xlsm
        合并公司
        对本期实现保费 排序
        添加序号
        拆分sheet
        注意表头

4. 步骤2
    对 {无保费}的表 进行处理
    参考 tmp步骤二结果.xlsm
        合并公司
        添加序号
        拆分sheet
        注意表头

5. 步骤3
    对 {团险}的表 进行处理
    参考 无保费 的结果
        合并公司
        按保费排序
        添加序号
        拆分sheet
        注意表头

6. 表头文字
    处理总表2得到：
        2022年前三季度，中国人民人寿保险股份有限公司（以下简称“人保寿险”）先后在我行上线5款产品，其中5款银保产品，0款私行产品，0款团险产品。
        我行代理该公司保费共21.02亿元，其中趸缴15.65亿元，期缴5.36亿元。
        主销产品情况：人保寿险鑫安两全保险(分红型)(C款)：15.64亿元，人保寿险臻鑫一生终身寿险：2.9亿元，共计18.54亿元，占代理该公司整体保费规模的88%。

    {中国人民人寿保险股份有限公司} ： {保险公司}
    {人保寿险}： {实际简称}
    统计信息： {产品目录.xlsx} 的 {统计（按名称）} sheet
        为空表示0，则不在文字体现
    21.02：本期实现保费的求和
    趸缴15.65亿元，期缴5.36亿元：缴费方式筛选后求和
    主销产品情况：前两个保费最高的（先求和再取前两个）
    数字保留两位小数

7. 将三个子表合并
    1. 每个sheet是一个公司
    2. 有保费 | 团险 | 无保费
        有保费没有子表头，有总表头
        大部分公司没有团险
        无保费有子表头

8. 插入文字

======
到这一步之后每个公司一个sheet，得到一个总表
9. 给各个负责人
    1. 一个负责人一个excel
    2. 每个负责人看到的sheet是总表的子集
"""

"""
Sub 拆分()

'刘轶翔

    Dim wb As Workbook

    ' 打开要复制的工作簿
    Set wb = Workbooks.Open(ThisWorkbook.Path & "\总表.xlsm")

    ' 复制工作簿
    wb.SaveCopyAs ThisWorkbook.Path & "\【刘轶翔】产品后评价2023一季度.xlsm"
        ' 关闭原始工作簿和新工作簿
    wb.Close False


    Dim wb1 As Workbook
    Dim ws As Worksheet

    Set wb1 = Workbooks.Open(ThisWorkbook.Path & "\【刘轶翔】产品后评价2023一季度.xlsm")

      For Each ws In wb1.Worksheets
        If ws.Name <> "太平人寿" And ws.Name <> "利安人寿" And ws.Name <> "天安人寿" _
        And ws.Name <> "恒大人寿" And ws.Name <> "财信吉祥人寿" And ws.Name <> "招商局仁和人寿" _
        And ws.Name <> "弘康人寿" And ws.Name <> "新华人寿" Then
           Application.DisplayAlerts = False
           ws.Delete
           Application.DisplayAlerts = True
        End If
      Next ws


    '保存和关闭工作表
    wb1.Save
    wb1.Close



'李坤'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''



    ' 打开要复制的工作簿
    Set wb = Workbooks.Open(ThisWorkbook.Path & "\总表.xlsm")

    ' 复制工作簿
    wb.SaveCopyAs ThisWorkbook.Path & "\【李坤】产品后评价2023一季度.xlsm"
        ' 关闭原始工作簿和新工作簿
    wb.Close False


    Dim wb2 As Workbook

    Set wb2 = Workbooks.Open(ThisWorkbook.Path & "\【李坤】产品后评价2023一季度.xlsm")

      For Each ws In wb2.Worksheets
        If ws.Name <> "中华联合人寿" And ws.Name <> "东吴人寿" And ws.Name <> "华贵人寿" _
        And ws.Name <> "中意人寿" And ws.Name <> "英大泰和人寿" And ws.Name <> "珠江人寿" _
        And ws.Name <> "中韩人寿" And ws.Name <> "北京人寿" And ws.Name <> "海保人寿" Then
           Application.DisplayAlerts = False
           ws.Delete
           Application.DisplayAlerts = True
        End If
      Next ws


    '保存工作表
    wb2.Save
    wb2.Close
'黄瑞'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''



    ' 打开要复制的工作簿
    Set wb = Workbooks.Open(ThisWorkbook.Path & "\总表.xlsm")

    ' 复制工作簿
    wb.SaveCopyAs ThisWorkbook.Path & "\【黄瑞】产品后评价2023一季度.xlsm"
        ' 关闭原始工作簿和新工作簿
    wb.Close False


    Dim wb3 As Workbook

    Set wb3 = Workbooks.Open(ThisWorkbook.Path & "\【黄瑞】产品后评价2023一季度.xlsm")

      For Each ws In wb3.Worksheets
        If ws.Name <> "人保寿险" And ws.Name <> "太平洋人寿" And ws.Name <> "君康人寿" _
        And ws.Name <> "合众人寿" And ws.Name <> "渤海人寿" And ws.Name <> "人保健康" _
        And ws.Name <> "中英人寿" And ws.Name <> "国华人寿" Then
           Application.DisplayAlerts = False
           ws.Delete
           Application.DisplayAlerts = True
        End If
      Next ws


    '保存工作表
    wb3.Save
    wb3.Close

'李关义'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''



    ' 打开要复制的工作簿
    Set wb = Workbooks.Open(ThisWorkbook.Path & "\总表.xlsm")

    ' 复制工作簿
    wb.SaveCopyAs ThisWorkbook.Path & "\【李关义】产品后评价2023一季度.xlsm"
        ' 关闭原始工作簿和新工作簿
    wb.Close False


    Dim wb4 As Workbook

    Set wb4 = Workbooks.Open(ThisWorkbook.Path & "\【李关义】产品后评价2023一季度.xlsm")

      For Each ws In wb4.Worksheets
        If ws.Name <> "平安人寿" And ws.Name <> "大家人寿" And ws.Name <> "和谐健康" _
        And ws.Name <> "国联人寿" And ws.Name <> "信泰人寿" And ws.Name <> "和泰人寿" _
        And ws.Name <> "国富人寿" And ws.Name <> "中信保诚" Then
           Application.DisplayAlerts = False
           ws.Delete
           Application.DisplayAlerts = True
        End If
      Next ws


    '保存工作表
    wb4.Save
    wb4.Close


 '刘昕龙'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''



    ' 打开要复制的工作簿
    Set wb = Workbooks.Open(ThisWorkbook.Path & "\总表.xlsm")

    ' 复制工作簿
    wb.SaveCopyAs ThisWorkbook.Path & "\【刘昕龙】产品后评价2023一季度.xlsm"
        ' 关闭原始工作簿和新工作簿
    wb.Close False


    Dim wb5 As Workbook

    Set wb5 = Workbooks.Open(ThisWorkbook.Path & "\【刘昕龙】产品后评价2023一季度.xlsm")

      For Each ws In wb5.Worksheets
        If ws.Name <> "农银人寿" And ws.Name <> "泰康人寿" And ws.Name <> "富德生命人寿" _
        And ws.Name <> "百年人寿" And ws.Name <> "中荷人寿" And ws.Name <> "爱心人寿" Then
           Application.DisplayAlerts = False
           ws.Delete
           Application.DisplayAlerts = True
        End If
      Next ws


    '保存工作表
    wb5.Save
    wb5.Close

'左萌'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''



    ' 打开要复制的工作簿
    Set wb = Workbooks.Open(ThisWorkbook.Path & "\总表.xlsm")

    ' 复制工作簿
    wb.SaveCopyAs ThisWorkbook.Path & "\【左萌】产品后评价2023一季度.xlsm"
        ' 关闭原始工作簿和新工作簿
    wb.Close False


    Dim wb6 As Workbook

    Set wb6 = Workbooks.Open(ThisWorkbook.Path & "\【左萌】产品后评价2023一季度.xlsm")

      For Each ws In wb6.Worksheets
        If ws.Name <> "中国人寿" And ws.Name <> "阳光人寿" And ws.Name <> "前海人寿" _
        And ws.Name <> "长城人寿" And ws.Name <> "幸福人寿" And ws.Name <> "长生人寿" _
        And ws.Name <> "复星保德信" Then
           Application.DisplayAlerts = False
           ws.Delete
           Application.DisplayAlerts = True
        End If
      Next ws


    '保存工作表
    wb6.Save
    wb6.Close


'孟醒'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''



    ' 打开要复制的工作簿
    Set wb = Workbooks.Open(ThisWorkbook.Path & "\总表.xlsm")

    ' 复制工作簿
    wb.SaveCopyAs ThisWorkbook.Path & "\【孟醒】产品后评价2023一季度.xlsm"
        ' 关闭原始工作簿和新工作簿
    wb.Close False


    Dim wb7 As Workbook

    Set wb7 = Workbooks.Open(ThisWorkbook.Path & "\【孟醒】产品后评价2023一季度.xlsm")

      For Each ws In wb7.Worksheets
        If ws.Name <> "华夏人寿" And ws.Name <> "昆仑健康" And ws.Name <> "三峡人寿" _
        And ws.Name <> "国宝人寿" And ws.Name <> "上海人寿" And ws.Name <> "横琴人寿" _
        And ws.Name <> "国民养老" And ws.Name <> "鼎诚人寿" Then
           Application.DisplayAlerts = False
           ws.Delete
           Application.DisplayAlerts = True
        End If
      Next ws


    '保存工作表
    wb7.Save
    wb7.Close
     MsgBox "已完成6-已生成评价文件", vbOKOnly
End Sub

"""
