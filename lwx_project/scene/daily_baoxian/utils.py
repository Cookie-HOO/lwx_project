

from lwx_project.scene.daily_baoxian.const import AREA_CODE_PATH
import pandas as pd
import os

# 缓存区划数据
_area_data_cache = None

def find_city_for_buyer_name(province, buyer_name, title):
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
    global _area_data_cache
    
    # 加载区划数据（使用缓存）
    if _area_data_cache is None:
        if os.path.exists(AREA_CODE_PATH):
            _area_data_cache = pd.read_csv(AREA_CODE_PATH)
        else:
            # 如果文件不存在，返回空
            return ""
    
    # 直辖市列表
    municipalities = ["北京市", "上海市", "天津市", "重庆市"]
    
    # 清理文本函数：移除末尾的省、市、区、自治区
    def clean_text(text):
        if not text:
            return ""
        # 按长度降序排列，确保最长的后缀优先被替换
        suffixes = ["自治区", "省", "市", "区"]
        for suffix in suffixes:
            if text.endswith(suffix):
                return text[:-len(suffix)]
        return text
    
    # 获取省份及其下辖单位 todo: 尝试把所有省份的索引缓存（看搜索时间）
    def get_province_data(province_name):
        # 1. 找出所有 level == 1 的行，并筛选出 area 包含 province_name 的行
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
    def get_cities_in_province(province_data, is_municipality):
        if is_municipality:
            # 直辖市的地级市是 level=3
            return province_data[province_data['level'] == 3]
        else:
            # 非直辖市的地级市是 level=2
            return province_data[province_data['level'] == 2]
    
    # 检查是否包含地级市
    def has_city_in_text(cities_data, text1, text2):
        for _, row in cities_data.iterrows():
            city_name = row['area']
            clean_city = clean_text(city_name)
            if (text1 and clean_city in text1) or (text2 and clean_city in text2):
                return True, row['area']
        return False, ""
    
    # 获取区域对应的地级市
    def get_city_for_area(area_name, province_data=None):
        # 确定搜索范围
        search_data = province_data if province_data is not None else _area_data_cache
        
        # 找到区域的位置
        area_idx = None
        for idx, row in search_data.iterrows():
            if clean_text(row['area']) == clean_text(area_name):
                area_idx = idx
                break
        
        if area_idx is None:
            return ""
        
        # 向上查找对应的地级市
        for idx in range(area_idx - 1, -1, -1):
            row = search_data.iloc[idx]
            # 对于直辖市，地级市是level=3；对于其他地区，地级市是level=2
            if (search_data.iloc[0]['area'] in municipalities and row['level'] == 3) or \
               (search_data.iloc[0]['area'] not in municipalities and row['level'] == 2):
                return row['area']
        
        return ""
    
    # 处理省份存在的情况
    if province and province.strip():
        # 1. 找到对应省份的所有内容
        province_name, province_data = get_province_data(province)
        
        if province_data is not None:
            # 是直辖市的情况
            is_municipality = province_name in municipalities
            
            # 2. 遍历该省份所有的地级市，检查是否在采购人名称或标题中
            cities_data = get_cities_in_province(province_data, is_municipality)
            has_city, _ = has_city_in_text(cities_data, buyer_name, title)
            
            if has_city:
                # 如果包含地级市，跳过该招标条目
                return ""
            
            # 3. 对于无法跳过的招标条目，遍历县级市、城、乡、街道
            lower_levels = [3, 4, 5]  # 县级市、街道、社区
            if is_municipality:
                # 直辖市的县级市是 level=4
                lower_levels = [4, 5]
            
            for level in lower_levels:
                level_data = province_data[province_data['level'] == level]
                for _, row in level_data.iterrows():
                    area_name = row['area']
                    clean_area = clean_text(area_name)
                    if (buyer_name and clean_area in buyer_name) or (title and clean_area in title):
                        # 找到对应的地级市
                        city = get_city_for_area(area_name, province_data)
                        if city:
                            return city
    
    # 处理省份不存在的情况
    # 1. 遍历所有的地级市，如果存在任意地级市在采购人名称或标题中，跳过该招标条目
    all_city_data = []
    for _, row in _area_data_cache.iterrows():
        # 直辖市的地级市是level=3，非直辖市的地级市是level=2
        if (row['area'] in municipalities and row['level'] == 3) or \
           (row['area'] not in municipalities and row['level'] == 2):
            all_city_data.append(row)
    
    for row in all_city_data:
        city_name = row['area']
        clean_city = clean_text(city_name)
        if (buyer_name and clean_city in buyer_name) or (title and clean_city in title):
            # 如果包含地级市，跳过该招标条目
            return ""
    
    # 2. 对于无法跳过的招标条目，遍历县级市、街道、社区
    lower_level_data = _area_data_cache[(_area_data_cache['level'] == 3) | \
                                        (_area_data_cache['level'] == 4) | \
                                        (_area_data_cache['level'] == 5)]
    
    for _, row in lower_level_data.iterrows():
        area_name = row['area']
        clean_area = clean_text(area_name)
        if (buyer_name and clean_area in buyer_name) or (title and clean_area in title):
            # 找到对应的地级市
            city = get_city_for_area(area_name)
            if city:
                return city
    
    return ""


if __name__ == '__main__':
    x = find_city_for_buyer_name("山东", "莱州市人民政府", "招标公告")
    print(x)