import typing

import pandas as pd
import os


from lwx_project.scene.monthly_communication_data.check_excel import UploadInfo
from lwx_project.utils.time_cost import time_cost


# 核心的分组计算过程: 依赖核心团险数据表的结构
@time_cost
def detail_group_by(upload_info: UploadInfo, code_map: dict,
                    after_one_done_callback: typing.Callable[[int], None] = None):
    """
    upload_info:
    code_map: 计算汇总结果时需要忽略或增加的代码，负数为忽略，正数为增加，绝对值为代码
        {
            "意外险": [],
            "健康险": [-7824],
            "寿险": [],
            "医疗基金": [+7824, +7854],
            "年金险": [-2801]
        }

    针对每一个excel执行下列过程（注意这里的每个excel可能在10mb左右，需要注意性能）：
        1. 读取第一个sheet
        2. 仅保留三列（第一行就是列名）
            ”机构名称”、“险种代码”、“保费收入/支出（含税）”
        3. 提取结构名称的前两个字符，如果前两个字符为“黑龙”，就补成 “黑龙江”，变成“分公司”列
            此时可以删掉机构名称列
        4. 按照“分公司”列进行groupby计算
            意外险：险种代码 以68开头 的行
            健康险：险种代码 以78开头，但是不包括7824 的行
                这里的7824是由 code_map 变量决定的，动态传入的，7824只是举个例子
            寿险: 意外险：险种代码 以18开头 的行
            医疗基金：险种代码 是7824 的行
                这里的7824是由 code_map 变量决定的，动态传入的，7824只是举个例子
            合计：上述四种保险的合计
            计算上述四种保险的价格：即 求和 保费收入/支出（含税） 列
                即每个分公司需要按照对应条件筛选后，对 保费收入/支出（含税） 列求和

            再增加一个年金险（算合计时不考虑）
                28开头，不考虑2801
        5. 最终生成的表格就是，第一列是groupby的分公司，后面6列是对应的四种保险的汇总以及合计 再加年金险
            共7列
    每个excel返回6列的一个dataframe
    """
    result_dfs = []
    upload_tuanxian_month_dict = upload_info.upload_tuanxian_month_dict
    excel_path_list = upload_tuanxian_month_dict.values()
    # 验证excel_path_list不为空
    if not excel_path_list:
        return result_dfs

    # 验证code_map的基本结构
    required_keys = ["意外险", "健康险", "寿险", "医疗基金"]
    for key in required_keys:
        if key not in code_map:
            code_map[key] = []

    month_sorted = sorted(upload_tuanxian_month_dict.keys())
    for month in month_sorted:
        excel_path = upload_tuanxian_month_dict[month]
        try:
            # 检查文件是否存在
            if not os.path.exists(excel_path):
                print(f"警告：文件不存在: {excel_path}")
                continue

            # 检查文件是否为Excel文件
            if not (excel_path.endswith('.xlsx') or excel_path.endswith('.xls')):
                print(f"警告：文件不是Excel文件: {excel_path}")
                continue

            # 读取Excel文件的第一个sheet，优化性能
            df = pd.read_excel(excel_path, sheet_name=0, engine='openpyxl', usecols=None)

            # 只保留需要的三列
            columns_to_keep = [
                '机构名称',  # 可能需要处理全角引号
                '险种代码',
                '保费收入/支出（含税）'
            ]

            # 处理可能的列名不一致问题
            actual_columns = []
            for col in columns_to_keep:
                found = False
                for actual_col in df.columns:
                    # 处理可能的全角字符和空格问题
                    clean_actual_col = ''.join(char for char in str(actual_col) if char.isprintable()).strip()
                    clean_target_col = ''.join(char for char in col if char.isprintable()).strip()

                    if clean_target_col in clean_actual_col or clean_actual_col in clean_target_col:
                        actual_columns.append(actual_col)
                        found = True
                        break
                if not found:
                    # 如果找不到完全匹配的列，尝试找到最相似的
                    for actual_col in df.columns:
                        clean_actual_col = ''.join(char for char in str(actual_col) if char.isprintable()).strip()
                        if any(keyword in clean_actual_col for keyword in ['机构', '险种', '保费']):
                            actual_columns.append(actual_col)
                            found = True
                            break
                if not found:
                    raise ValueError(f"在Excel文件中找不到列: {col}")

            # 重命名列以便后续处理
            df = df[actual_columns].copy()
            df.columns = columns_to_keep

            # 创建"分公司"列
            def process_company_name(name):
                if isinstance(name, str):
                    if len(name) >= 2:
                        first_two = name[:2]
                        if first_two == '黑龙':
                            return '黑龙江'
                        return first_two
                return str(name)[:2] if isinstance(name, str) else str(name)

            df['分公司'] = df['机构名称'].apply(process_company_name)

            # 移除"机构名称"列
            df = df.drop('机构名称', axis=1)

            # 确保"险种代码"是字符串类型
            df['险种代码'] = df['险种代码'].astype(str)

            # 确保"保费收入/支出（含税）"是数值类型
            df['保费收入/支出（含税）'] = pd.to_numeric(df['保费收入/支出（含税）'], errors='coerce')
            df = df.dropna(subset=['保费收入/支出（含税）'])

            # 准备分组计算
            grouped = df.groupby('分公司')
            result_df = pd.DataFrame()
            result_df['分公司'] = list(grouped.groups.keys())

            # 计算各种保险类型的保费总和

            # 1. 意外险计算
            # 基础条件：险种代码必须以68开头
            # 从code_map['意外险']中获取所有正数代码（表示额外包含的代码）和负数代码（表示要排除的代码）
            include_accident_codes = [str(abs(code)) for code in code_map.get('意外险', []) if code > 0]
            exclude_accident_codes = [str(abs(code)) for code in code_map.get('意外险', []) if code < 0]

            accident_insurance = grouped.apply(
                lambda x: x[
                    # 必须满足基础条件：以68开头
                    (x['险种代码'].str.startswith('68', na=False)) &
                    # 额外包含的代码（如果有）
                    ((len(include_accident_codes) == 0) | (x['险种代码'].isin(include_accident_codes))) &
                    # 排除指定的代码
                    (~x['险种代码'].isin(exclude_accident_codes))
                    ]['保费收入/支出（含税）'].sum()
            )

            # 2. 健康险计算
            # 基础条件：险种代码必须以78开头
            # 从code_map['健康险']中获取所有正数代码（表示额外包含的代码）和负数代码（表示要排除的代码）
            include_health_codes = [str(abs(code)) for code in code_map.get('健康险', []) if code > 0]
            exclude_health_codes = [str(abs(code)) for code in code_map.get('健康险', []) if code < 0]

            health_insurance = grouped.apply(
                lambda x: x[
                    # 必须满足基础条件：以78开头
                    (x['险种代码'].str.startswith('78', na=False)) &
                    # 额外包含的代码（如果有）
                    ((len(include_health_codes) == 0) | (x['险种代码'].isin(include_health_codes))) &
                    # 排除指定的代码
                    (~x['险种代码'].isin(exclude_health_codes))
                    ]['保费收入/支出（含税）'].sum()
            )

            # 3. 寿险计算
            # 基础条件：险种代码必须以18开头
            # 从code_map['寿险']中获取所有正数代码（表示额外包含的代码）和负数代码（表示要排除的代码）
            include_life_codes = [str(abs(code)) for code in code_map.get('寿险', []) if code > 0]
            exclude_life_codes = [str(abs(code)) for code in code_map.get('寿险', []) if code < 0]

            life_insurance = grouped.apply(
                lambda x: x[
                    # 必须满足基础条件：以18开头
                    (x['险种代码'].str.startswith('18', na=False)) &
                    # 额外包含的代码（如果有）
                    ((len(include_life_codes) == 0) | (x['险种代码'].isin(include_life_codes))) &
                    # 排除指定的代码
                    (~x['险种代码'].isin(exclude_life_codes))
                    ]['保费收入/支出（含税）'].sum()
            )

            # 4. 医疗基金计算
            # 从code_map['医疗基金']中获取所有正数代码（表示要包含的代码）和负数代码（表示要排除的代码）
            include_medical_codes = [str(abs(code)) for code in code_map.get('医疗基金', []) if code > 0]
            exclude_medical_codes = [str(abs(code)) for code in code_map.get('医疗基金', []) if code < 0]

            medical_fund = grouped.apply(
                lambda x: x[
                    # 必须满足包含条件
                    (x['险种代码'].isin(include_medical_codes)) &
                    # 排除指定的代码
                    (~x['险种代码'].isin(exclude_medical_codes))
                    ]['保费收入/支出（含税）'].sum()
            )

            # 计算合计
            total = accident_insurance + health_insurance + life_insurance + medical_fund

            # 5. 年金险（需要单独算合计，不和其他类型一起）
            include_annu_codes = [str(abs(code)) for code in code_map.get('年金险', []) if code > 0]
            exclude_annu_codes = [str(abs(code)) for code in code_map.get('年金险', []) if code < 0]

            annu_fund = grouped.apply(
                lambda x: x[
                    # 必须满足基础条件：以28开头
                    (x['险种代码'].str.startswith('28', na=False)) &
                    # 额外包含的代码（如果有）
                    ((len(include_annu_codes) == 0) | (x['险种代码'].isin(include_annu_codes))) &
                    # 排除指定的代码
                    (~x['险种代码'].isin(exclude_annu_codes))
                    ]['保费收入/支出（含税）'].sum()
            )

            # 将计算结果添加到结果DataFrame
            result_df = result_df.set_index('分公司')
            result_df['意外险'] = accident_insurance
            result_df['健康险'] = health_insurance
            result_df['寿险'] = life_insurance
            result_df['医疗基金'] = medical_fund
            result_df['短期合计'] = total
            result_df['年金险'] = annu_fund
            result_df['长期合计'] = annu_fund  # 长期其他都是0
            # 金额单位转换：除以10000，保留两位小数
            amount_columns = ['意外险', '健康险', '寿险', '医疗基金', '短期合计', '年金险', "长期合计"]
            for col in amount_columns:
                result_df[col] = (result_df[col] / 10000).round(2)

            # 重置索引，使分公司成为普通列
            result_df = result_df.reset_index()

            # 填充可能的NaN值为0
            result_df = result_df.fillna(0)

            result_dfs.append(result_df)
        except Exception as e:
            print(f"处理文件 {excel_path} 时出错: {str(e)}")
            continue
        finally:
            if after_one_done_callback is not None:
                after_one_done_callback(month)
    return result_dfs

