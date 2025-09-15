import typing

from lwx_project.scene.daily_baoxian.const import AREA_CODE_PATH
import pandas as pd
import os

# 缓存区划数据
_area_data_cache: typing.Optional[pd.DataFrame] = None

# 直辖市列表
municipalities = ["北京市", "上海市", "天津市", "重庆市", "北京", "上海", "天津", "重庆"]


# 获取省份及其下辖单位
def helper_get_province_data(province_name):
    """输入省名称，找到省级单位下辖的所有数据
    """
    # 1. 找出所有 level == 1 的行，并筛选出 area 包含 province_name 的行
    if _area_data_cache is None:
        return None, None
    level_1_mask = _area_data_cache['level'] == 1
    level_1_rows = _area_data_cache[level_1_mask]

    # 使用向量化子串匹配（不区分大小写可选，根据需求加 case=False）
    match_mask = level_1_rows['area'].str.contains(province_name, na=False, regex=False)
    matched_level_1 = level_1_rows[match_mask]

    if matched_level_1.empty:
        return None, None

    # 取第一个匹配的省份（假设名称唯一或取首个最匹配）
    start_idx = matched_level_1.index[0]  # 第一个匹配项在原 DataFrame 中的索引

    # 2. 找到下一个 level == 1 的索引（即结束位置）
    # 获取所有 level == 1 的索引（已排序，因为 _area_data_cache 是层级有序的）
    all_level_1_indices = level_1_rows.index.tolist()

    # 在这些索引中，找到第一个大于 start_idx 的索引
    next_idx = None
    for idx in all_level_1_indices:
        if idx > start_idx:
            next_idx = idx
            break

    end_idx = next_idx if next_idx is not None else len(_area_data_cache)

    # 3. 截取数据块
    province_data = _area_data_cache.iloc[start_idx:end_idx]
    return province_name, province_data

# 获取省份下的地级市
def helper_get_cities_in_province(province_data: pd.DataFrame, is_municipality) -> pd.DataFrame:
    """输入该省下辖的所有数据，以及是否是直辖市的标记位
    输出：地级市的row
    """
    if is_municipality:
        # 直辖市的地级市是 level=3
        return province_data[province_data['level'] == 3]
    else:
        # 非直辖市的地级市是 level=2
        return province_data[province_data['level'] == 2]


# 检查是否包含地级市
def helper_has_city_in_text(cities_data: pd.DataFrame, text1, text2):
    # 向量化清洗所有城市名，去除空值
    cities_clean = cities_data['area'].apply(helper_clean_text).dropna().tolist()

    if not cities_clean:
        return False, ""

    # 短路查找：第一个匹配的城市，不用apply，是因为找到一个就可以停了
    for city in cities_clean:
        if (text1 and city in text1) or (text2 and city in text2):
            return True, city

    return False, ""


# 清理文本函数：移除末尾的省、市、区、自治区
def helper_clean_text(text):
    if not text:
        return ""
    # 按长度降序排列，确保最长的后缀优先被替换
    suffixes = ["自治区", "省", "市", "区"]
    for suffix in suffixes:
        if text.endswith(suffix):
            return text[:-len(suffix)]
    return text

# 获取区域对应的地级市
def helper_get_city_for_area(area_name, search_data=None):
    if not area_name or not isinstance(area_name, str):
        return ""

    search_data = search_data if search_data is not None else _area_data_cache
    clean_target = helper_clean_text(area_name)

    # 向量化清洗整个列（只做一次）
    search_data = search_data.copy()
    search_data['clean_area'] = search_data['area'].apply(helper_clean_text)

    # 找到目标区域的索引位置
    match_idx = search_data[search_data['clean_area'] == clean_target].index
    if len(match_idx) == 0:
        return ""

    start_idx = match_idx[0]

    # 向上查找第一个满足条件的地级市
    target_level = 3 if search_data.iloc[0]['area'] in municipalities else 2

    # 从 start_idx 往前扫描（已排序，所以向上就是索引递减）
    for idx in range(start_idx, -1, -1):
        try:
            row = search_data.loc[idx]
        except Exception as e:
            pass
        if row['level'] == target_level:
            return row['area']

    return ""

def helper_find_city_from_lower_levels(province_data: pd.DataFrame, buyer_name: str, title: str, is_municipality: bool):
    """
    在 province_data 中查找是否有县级市/街道/社区名出现在 buyer_name 或 title 中，
    如果有，返回其所属地级市（通过 level=2 的父节点映射）
    """

    # 1. 定义目标层级：根据是否为直辖市调整
    lower_levels = [4, 5] if is_municipality else [3, 4, 5]

    # 2. 只提取所有目标层级的数据（一次性过滤，避免多次 df[df['level']==x]）
    target_mask = province_data['level'].isin(lower_levels)
    lower_data = province_data[target_mask].copy()

    if len(lower_data) == 0:
        return None

    # 3. 向量化清洗所有区域名称（apply 是向量化的！）
    lower_data['clean_area'] = lower_data['area'].apply(helper_clean_text)

    # 4. 构造匹配条件：检查 clean_area 是否在 buyer_name 或 title 中
    # 注意：这里不能直接向量化 'in'，但我们可以用生成器 + any() 实现短路
    # 我们不构造完整布尔数组，而是逐个检查并短路返回

    for _, row in lower_data.iterrows():
        clean_area = row['clean_area']
        if (buyer_name and clean_area in buyer_name) or (title and clean_area in title):
            # 找到匹配项，立即返回其所属地级市
            return helper_get_city_for_area(row['area'], province_data)

    return None


def find_city_for_buyer_name_with_province(province, buyer_name, title):
    """关键方法
    给定province的情况下，基于 buyer_name, title 寻找地级市
    """
    if province is None or (isinstance(province, str) and len(province.strip()) == 0):
        return ""

    # 1. 找到对应省份的所有内容
    province_name, province_data = helper_get_province_data(province)

    if province_data is not None:
        # 是直辖市的情况
        is_municipality = province_name in municipalities

        # 2. 遍历该省份所有的地级市，检查是否在采购人名称或标题中
        cities_data = helper_get_cities_in_province(province_data, is_municipality)
        has_city, _ = helper_has_city_in_text(cities_data, buyer_name, title)

        if has_city:
            # 如果包含地级市，跳过该招标条目
            return ""

        # 3. 对于无法跳过的招标条目，遍历县级市、城、乡、街道
        # 3.1. 定义目标层级：根据是否为直辖市调整
        lower_levels = [4, 5] if is_municipality else [3, 4, 5]

        # 3.2. 只提取所有目标层级的数据（一次性过滤，避免多次 df[df['level']==x]）
        target_mask = province_data['level'].isin(lower_levels)
        lower_data = province_data[target_mask].copy()

        if len(lower_data) == 0:
            return ""

        # 3.3 向量化清洗所有区域名称（apply 是向量化的！）
        lower_data['clean_area'] = lower_data['area'].apply(helper_clean_text)

        # 3.4. 构造匹配条件：检查 clean_area 是否在 buyer_name 或 title 中
        # 注意：这里不能直接向量化 'in'，但我们可以用生成器 + any() 实现短路
        # 我们不构造完整布尔数组，而是逐个检查并短路返回

        for _, row in lower_data.iterrows():
            clean_area = row['clean_area']
            if (buyer_name and clean_area in buyer_name) or (title and clean_area in title):
                # 找到匹配项，立即返回其所属地级市
                return helper_get_city_for_area(row['area'], province_data)

    # 省份存在但没有找到
    return ""

def find_city_for_buyer_name(province, buyer_name, title) -> (str, str):
    """在采购人名称中增加地级市（如果采购人名称中没有地级市的话）
    第一步. 加载区划统计表（这个表只需要加载一次，后续走缓存，15mb左右的csv）
    第二步. 如果该条目存在省份
        1. 按照省份进行过滤（找到对应省份的所有内容）
            即找到 level=1中的行，然后遍历判断，province 是否在 area字段中
        2. 遍历该省份所有的地级市，如果存在任意地级市在采购人名称或标题中，跳过该招标条目
            即找到对应省份下的地级市，然后遍历地级市，判断地级市的area名称，是否 in 采购人名称或标题中
            判断前需要注意：把末尾的“省” “市” “区” “自治区” 删掉再判断
        3. 对于无法跳过的招标条目
            在对应省份下按顺序遍历县级市、城、乡、街道，如果出现在采购人名称或标题中，就返回对应的地级市，同时停止搜索
            判断前需要注意：把末尾的“省” “市” “区” “自治区” 删掉再判断
    第三步. 如果该条目不存在省份
        无法按照省份进行过滤了，但是保留第二步的其他内容（判断方法也需要保留），即：
        1. 遍历所有的地级市，如果存在任意地级市在采购人名称或标题中，跳过该招标条目
        2. 对于无法跳过的招标条目
            按顺序遍历县级市、街道、社区，如果出现在采购人名称或标题中，就返回对应的地级市，同时停止搜索
    补充信息
        1. AREA_CODE_PATH 变量存储了 区划统计表的路径，csv格式
            area列表示名称、level列表示级别
            存储举例：
                area   level
                北京市  1
                市辖区  2
                东城区  3
                西城区  3
            level：
                1 表示省或直辖市
                2 表示地级市，但注意，如果是直辖市的话，那么3表示地级市，比如对于北京来说，3是地级市
                    直辖市：北京市、上海市、天津市、重庆市
                3 表示县级市，如果是直辖市的话，3表示地级市
                4 街道
                5 社区
        2. 所有的数据就是两列，如果要找某一个省下面的所有下辖单位，那么，需要从这个省份开始遍历，直到遍历到下一个省份
            这两个省份之间的内容，就是这个省份下辖的单位
            找到某一个市下面的所有单位同理（即：两个level一致的行，中间夹的就是）
    """
    # 1. 输入校验
    if not buyer_name or not title:
        return province, ""

    # 2. 读取数据（用于缓存）
    global _area_data_cache
    if _area_data_cache is None:
        if os.path.exists(AREA_CODE_PATH):
            _area_data_cache = pd.read_csv(AREA_CODE_PATH)
        else:
            # 如果文件不存在，返回空
            return province, ""

    # 3. 如果给定了province
    if province and len(province.strip()) > 0:
        res = find_city_for_buyer_name_with_province(province, buyer_name, title)
        return province, res

    # 4. 如果没给定province，找到所有province，每一个进行执行
    all_province = _area_data_cache[_area_data_cache['level'] == 1]["area"]
    for area in all_province:
        res = find_city_for_buyer_name_with_province(area, buyer_name, title)
        if res:
            return area, res
    return "", ""


if __name__ == '__main__':
    x = find_city_for_buyer_name("辽宁", " 中国医科大学附属盛京医院", "员工大病意外综合保险招标项目招标公告")
    print(x)