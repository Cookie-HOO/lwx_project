"""
第一步：基础筛选：对于path对应的excel表，进行基础筛选
    1. {团/卡单业务} 筛选 团体保单
    2. 过滤掉 {险种代码}  等于 7824、2801、7854【需要配置】的行
        在这个函数中，需要传入一个列表，列表中的元素是要忽略的险种代码
    3. {保全号} 筛选 为空的行
    4. {业务性质} 筛选 {农行赠险业务}、{农行员福业务}
        不再筛选了，保留所有的行

第二步：进一步筛选得到以下两种类型的数据：
    1. 得到农行的关联交易数据
        1. {团体客户名称} 包含“中国农业银行”
    
    2. 得到其他关联方的交易数据
        1. 在 connection_name_path 存储的excel 中，读取第一列（没有列名，直接是所有的名称
            就一列直接是名字，没有列名
        2. {团体客户名称} 筛选 在 上传的名字里面的行

第三步：准备其他数据
    1. TEMPLATE_PATH 变量中存储的excel，读取“*交易协议名称” 列
        格式如下：
            农行员福保险合同2025-249，获取最大的一个数字，对应农行的最大数字（后面要用）
            其他关联方员福保险合同2025-13，获取最大的一个数字，对应其他关联方的最大数字（后面要用）
    2. connection_name_path 变量存储的excel，读取第一列（没有列名，直接是所有的名称）
    3. connection_name_code_path 变量存储的excel，读取前两列（只有两列）
        {关联方名称}、{关联方代码} 列，存储映射关系
        通过名称寻找代码
        
第四步：针对第二步得到的两部分数据，groupby {保险单号} 进行汇总（配合第三部分得到的辅助数据）
    *交易协议名称
        农行的数据：
            格式如下：农行员福保险合同2025-249
            三部分：
                1. 文字保留
                2. 年份是传入的参数 year
                3. 数字读取最大的（第三步得到的农行的最大数字，然后加+1，系统中不能重复）
        其他关联方：
            格式如下：其他关联方员福保险合同2025-13
            要求同上（用其他关联方的最大数字，然后+1）
    *关联方类型
        固定值：“1法人及其他组织”
    *关联方名称
        {团体客户名称} 列 取第一个
    *关联方代码：数字格式
        农行的数据：911100001000054748
        其他关联方：用 {*关联方名称} 去 第三步得到的  {关联方名称}、{关联方代码} 列的映射关系找代码
    *业务类型
        固定值：“01保险业务”
    *合同编号
        就是 {保险单号} 列（groupby的列）
    *合同状态
        固定值：“有效”
    保单号：
        同{*合同编号}
    团个性质
        固定值：“团体保单”
    *合同签订日期
        {承保日期}列 取第一个
    *协议业务起始日期
        {日期}列 取第一个
    协议业务结束日期
        留空
    *货币代码
        固定值：“CNY”
    *交易金额（原币）	*交易金额（本位币）	*交易价格：这三列一样
        三列值都是：{保费收入/支出(不含税)}列的数字求和
    *定价政策
        固定值：“市场公允价格”
    *交易概述	*交易标的：这两列一样
        groupby之后，取 {业务性质}列的第一行
            如果是 “农行赠险业务”，这里写“为客户投保的团险产品”
            如果是 “农行员福业务”，这里写“为员工投保的团险产品”
    *单笔关联交易类型
        农行的row：
            “重大关联交易”
        其他关联方的row
            “一般关联交易”
    达到重大关联交易的情形
        固定值：“单笔达到”
    *统一交易协议标志
        固定值：“0否”
    其他说明事项
        留空
    *补充协议标志
        固定值：“0否”
    主合同编号
        留空

"""
import os
import re
import pandas as pd

from lwx_project.scene.monthly_east_data.utils import get_name_code_map, get_name, \
    build_east_result_path_from_year_month
from lwx_project.scene.monthly_east_data.const import TEMPLATE_PATH, DETAIL_PATH

from lwx_project.utils.calculator import num_or_na_or_zero
from lwx_project.utils.year_month_obj import YearMonth


class CalExcelOneInfo:
    def __init__(self):
        # 原始数据
        self.raw_row_count = None  # 原始行数
        self.after_filter_count = None  # 基础过滤之后的值
        self.abc_count = None  # 某列=特定值
        self.other_count = None  # 需要在名称list中，且不是abc的

        self.year_month_obj: YearMonth = YearMonth()  # 根据日期得到的年月
        self.target_file_name = None  # 保存的名字

        self.max_abc_num = None
        self.max_other_num = None

        self._raw_df = None  # 原始df
        self._df_abc = None
        self._df_other = None
        self._df_result = None


def baoxian_order_code_groupby(path, cur_year_month: YearMonth, omit_baoxian_code_list, year, connection_name_path, connection_name_code_path) -> CalExcelOneInfo:
    """
    path: 团险数据的路径
    omit_baoxian_code_list: 要忽略的险种列表
    year: 年
    connection_name_path: 关联方名称的件路径
    connection_name_code_path: 关联方名称和代码的映射文件路径
    """
    # 1. 第一步：基础筛选：对于path对应的excel表，进行基础筛选
    cal_excel_one_info = base_filter(path, omit_baoxian_code_list)

    # 2. 第二步：进一步筛选得到以下两种类型的数据
    cal_excel_one_info= further_filter(cal_excel_one_info, connection_name_path)

    # 3. 第三步：准备其他数据
    max_abc_num, max_other_num, connection_name, connection_name_code = prepare_data(
        cur_year_month, connection_name_path, connection_name_code_path
    )

    # 4. 第四步：针对第二步得到的两部分数据，groupby {保险单号} 进行汇总（配合第三部分得到的辅助数据）
    cal_excel_one_info = groupby_insurance_num(
        cal_excel_one_info, max_abc_num, max_other_num, connection_name, connection_name_code, year
    )

    return cal_excel_one_info


def base_filter(path, omit_baoxian_code_list) -> CalExcelOneInfo:
    """
    基础筛选函数
    :param path: Excel文件路径
    :param omit_baoxian_code_list: 要忽略的险种代码列表
    :return: 筛选后的DataFrame
    """
    cal_excel_one_info = CalExcelOneInfo()

    # 读取Excel文件
    df = pd.read_excel(path)
    cal_excel_one_info.raw_row_count = df.shape[0]
    
    # 1. 筛选 {团/卡单业务} 等于 团体保单 的行
    df = df[df['团/卡单业务'] == '团体保单']
    
    # 2. 过滤掉 {险种代码} 等于 忽略列表中的行
    # 确保险种代码是字符串类型后再进行过滤
    df['险种代码'] = df['险种代码'].astype(str)
    df = df[~df['险种代码'].isin([str(code) for code in omit_baoxian_code_list])]
    
    # 3. 筛选 {保全号} 为空的行
    df = df[df['保全号'].isna()]
    
    # 4. 筛选 {业务性质} 等于 {农行赠险业务} 或 {农行员福业务} 的行
    # df = df[df['业务性质'].isin(['农行赠险业务', '农行员福业务'])]

    cal_excel_one_info.after_filter_count = df.shape[0]
    cal_excel_one_info._raw_df = df
    return cal_excel_one_info


def further_filter(cal_excel_one_info: CalExcelOneInfo, connection_name_path) -> CalExcelOneInfo:
    """
    进一步筛选得到两种类型的数据
    :param cal_excel_one_info: 基础筛选后的DataFrame
    :param connection_name_path: 关联方名称文件路径
    :return: (df_abc, df_other) 农行数据和其他关联方数据
    """
    # 1. 得到农行的关联交易数据
    df = cal_excel_one_info._raw_df
    # 筛选 {团体客户名称} 包含“中国农业” 的行
    df_abc = df[df['团体客户名称'].str.contains('中国农业银行', na=False)]
    
    # 2. 得到其他关联方的交易数据
    # 读取关联方名称文件的第一列（没有列名）
    connection_name_df = pd.read_excel(connection_name_path, header=None)
    # 获取第一列的所有名称（转为字符串列表）
    connection_names = [str(name) for name in connection_name_df.iloc[:, 0].tolist()]
    
    # 筛选 {团体客户名称} 在关联方名称列表中的行
    # 排除已经属于农行的数据
    df_other = df[df['团体客户名称'].isin(connection_names) & ~df.index.isin(df_abc.index)]

    # 组装结果
    cal_excel_one_info._df_abc = df_abc
    cal_excel_one_info._df_other = df_other
    cal_excel_one_info.abc_count = df_abc.shape[0]
    cal_excel_one_info.other_count = df_other.shape[0]

    cal_excel_one_info._raw_df = None
    return cal_excel_one_info


def _get_max_num(cur_year_month: YearMonth):
    """
    abc和other 都可能需要递归往前找上个月对应的文件的最大数字
    """
    # 如果没有这个文件
    last_month_template_path = build_east_result_path_from_year_month(cur_year_month.sub_one_month())
    if not os.path.exists(last_month_template_path):
        return 0, 0  # max_abc_num, max_other_num

    # 如果有这个文件
    template_df = pd.read_excel(last_month_template_path, engine='openpyxl', sheet_name="关联交易协议实体")

    # 检查是否有“*交易协议名称”列
    if '*交易协议名称' in template_df.columns:
        # 分别提取农行和其他关联方的最大数字
        abc_pattern = re.compile(r'农行员福保险合同\d{4}-(\d+)')
        other_pattern = re.compile(r'其他关联方员福保险合同\d{4}-(\d+)')

        max_abc_num = 0
        max_other_num = 0

        # 找最大值
        for name in template_df['*交易协议名称'].dropna():
            abc_match = abc_pattern.search(str(name))
            other_match = other_pattern.search(str(name))

            if abc_match:
                this_abc_num = int(abc_match.group(1))
                if this_abc_num > max_abc_num:
                    max_abc_num = this_abc_num

            elif other_match:
                this_other_num = int(other_match.group(1))
                if this_other_num > max_other_num:
                    max_other_num = this_other_num

        # 最优：两个都不是0
        if max_abc_num != 0 and max_other_num != 0:
            return max_abc_num, max_other_num
        # 递归查找
        elif max_abc_num == 0:
            max_abc_num, _ = _get_max_num(cur_year_month.sub_one_month())
            return max_abc_num, max_other_num
        elif max_other_num == 0:
            _, max_other_num = _get_max_num(cur_year_month.sub_one_month())
            return max_abc_num, max_other_num
    return 0, 0

def prepare_data(cur_year_month, connection_name_path, connection_name_code_path):
    """
    准备其他数据
    :param cur_year_month: 当前的年月对象
    :param connection_name_path: 关联方名称文件路径
    :param connection_name_code_path: 关联方名称和代码的映射文件路径
    :return: (max_abc_num, max_other_num, connection_name, connection_name_code)
    """
    max_abc_num, max_other_num = _get_max_num(cur_year_month)
    
    # 2. 读取关联方名称文件的第一列
    connection_name = get_name(connection_name_path)

    # 3. 读取关联方名称和代码的映射文件
    connection_name_code = get_name_code_map(connection_name_code_path)

    return max_abc_num, max_other_num, connection_name, connection_name_code


def groupby_insurance_num(cal_excel_one_info: CalExcelOneInfo, max_abc_num, max_other_num, connection_name, connection_name_code, year) -> CalExcelOneInfo:
    """
    按保险单号分组汇总数据
    :param cal_excel_one_info: 包括 农行数据、其他关联方数据
    :param max_abc_num: 农行最大数字
    :param max_other_num: 其他关联方最大数字
    :param connection_name: 关联方名称列表
    :param connection_name_code: 关联方名称和代码的映射字典
    :param year: 年份
    :return: 汇总后的DataFrame
    """
    df_abc, df_other = cal_excel_one_info._df_abc, cal_excel_one_info._df_other
    # 定义汇总函数
    def groupby_func(df, is_abc=True):
        # 按保险单号分组
        grouped = df.groupby('保险单号')
        
        # 准备结果列表
        result_list = []
        current_num = max_abc_num if is_abc else max_other_num
        
        for group_name, group_data in grouped:
            current_num += 1
            
            # 获取第一行数据
            first_row = group_data.iloc[0]
            
            # 计算保费收入总和
            premium_sum = sum(num_or_na_or_zero(x) for x in group_data['保费收入/支出(不含税)'])
            
            # 构建结果行
            result_row = {
                '*交易协议名称': f'农行员福保险合同{year}-{current_num}' if is_abc else f'其他关联方员福保险合同{year}-{current_num}',
                '*关联方类型': '1法人及其他组织',
                '*关联方名称': first_row['团体客户名称'],
                '*关联方代码': '911100001000054748' if is_abc else connection_name_code.get(str(first_row['团体客户名称']), ''),
                '*业务类型': '01保险业务',
                '*合同编号': group_name,
                '*合同状态': '有效',
                '保单号': group_name,
                '团个性质': '团体保单',
                '*合同签订日期': first_row['承保日期'],
                '*协议业务起始日期': first_row['日期'],
                '协议业务结束日期': '',
                '*货币代码': 'CNY',
                '*交易金额（原币）': premium_sum,
                '*交易金额（本位币）': premium_sum,
                '*交易价格': premium_sum,
                '*定价政策': '市场公允价格',
                '*交易概述': '为客户投保的团险产品' if first_row['业务性质'] == '农行赠险业务' else '为员工投保的团险产品',
                '*交易标的': '为客户投保的团险产品' if first_row['业务性质'] == '农行赠险业务' else '为员工投保的团险产品',
                '*单笔关联交易类型': '重大关联交易' if is_abc else '一般关联交易',
                '达到重大关联交易的情形': '单笔达到',
                '*统一交易协议标志': '0否',
                '其他说明事项': '',
                '*补充协议标志': '0否',
                '主合同编号': ''
            }
            
            result_list.append(result_row)
        
        return pd.DataFrame(result_list)
    
    # 分别处理农行数据和其他关联方数据
    df_abc_result = groupby_func(df_abc, is_abc=True)
    df_other_result = groupby_func(df_other, is_abc=False)
    
    # 合并结果
    df_result = pd.concat([df_abc_result, df_other_result], ignore_index=True)

    cal_excel_one_info._df_result = df_result

    cal_excel_one_info._df_abc = None
    cal_excel_one_info._df_other = None
    cal_excel_one_info.max_abc_num = max_abc_num + df_abc_result.shape[0]
    cal_excel_one_info.max_other_num = max_other_num + df_other_result.shape[0]
    return cal_excel_one_info
