import re

import pandas as pd

from lwx_project.scene.daily_baoxian.const import REGRESSION_PATH, PROVINCES_ABBR, PROVINCES
from lwx_project.utils.strings import is_all_chinese

df = pd.read_csv(REGRESSION_PATH)

"""
序号
地区
采购方式
项目名称
采购单位名称
预算/限价（万元）
获取招标文件的截止日期
招采平台
链接
原标题
详情信息
"""

class BaoxianItem:
    def __init__(self, platform, title, bid_type):
        self.platform = platform
        self.title = title
        self.province = ""
        self.url = ""
        self.detail = ""
        self.publish_date = ""

        self.default_available = True
        self.not_available_reason = ""

        # 需要下载的内容
        self.simple_title: str = ""
        self.bid_type: str = bid_type
        self.buyer_name: str = ""
        self.budget: str = ""
        self.get_bid_until: str = ""

        self.success = True

    @staticmethod
    def get_province_abbr_first(content):
        for p in PROVINCES_ABBR + PROVINCES:  # 先找简称
            if content.startswith(p):
                return p
        return ""

    def parse_from_detail(self):
        pass

    def set_detail(self, detail):
        self.detail = detail
        self.parse_from_detail()
        return self

    # 正则匹配detail的工具函数
    def parse_detail(self, pattern, condition=None, extract_index=None, from_bottom_to_top=False) -> typing.Union[str, typing.Tuple[str]]:
        res = re.findall(pattern, self.detail, re.DOTALL)
        if not res:
            return ""
        if from_bottom_to_top:
            res = res[::-1]
        target = res[0]
        if condition is None:
            return target if extract_index is None else target[extract_index]
        for index, matched in enumerate(res):
            if condition(matched):
                return matched if extract_index is None else matched[extract_index]
        return ""

    def get_default_budget(self):
        parsed_budget = self.parse_detail("预\s*算\s*金\s*额\s*(.*?\d.*?)[\n(（]").strip().replace(" ", "").replace(":", "").replace("：", "").strip() or \
            self.parse_detail("项\s*目\s*预\s*算\s*(.*?\d.*?)[\n(（]").strip().replace(" ", "").replace(":", "").replace("：", "").strip()
        parsed_budget = parsed_budget.replace("(", "").replace(")", "").replace("（", "").replace("）", "").replace(":", "").replace("：", "").strip()
        try:
            if parsed_budget.endswith("万元") or parsed_budget.endswith("万元人民币") or parsed_budget.startswith("万元") or parsed_budget.startswith("万元人民币"):
                parsed_budget = parsed_budget.replace("万元人民币", "").replace("万元", "").strip()
                parsed_budget = str(float(parsed_budget.replace(",", "")))
            elif parsed_budget.endswith("元") or parsed_budget.endswith("元人民币") or (len(parsed_budget) > 0 and parsed_budget[-1].isdigit()) or parsed_budget.startswith("元") or parsed_budget.startswith("元人民币"):
                parsed_budget = parsed_budget.replace("元人民币", "").replace("元", "").strip()
                parsed_budget = str(float(parsed_budget.replace(",", "")) / 10000)
            else:
                pass
        except ValueError:
            pass
        return parsed_budget

    def get_default_get_bid_until(self):
        parsed_get_bid_until = self.parse_detail("获\s*取\s*招\s*标\s*文\s*件\s*\n.*?至(.*?)[日,，]", from_bottom_to_top=True).strip() or \
                               self.parse_detail("获\s*取\s*采\s*购\s*文\s*件\s*\n.*?至(.*?)[日,，]", from_bottom_to_top=True).strip() or \
                               self.parse_detail("获\s*取\s*竞\s*争\s*性\s*磋\s*商\s*文\s*件\s*\n.*?至(.*?)[日,，]", from_bottom_to_top=True).strip() or \
                               self.parse_detail("获\s*取\s*.{1,8}文\s*件\s*\n.*?至(.*?)[日,，]", from_bottom_to_top=True).strip()

        get_bid_until = parsed_get_bid_until.replace("年", "/").replace("月", "/").replace("-", "/")
        return get_bid_until

    def get_default_simple_title(self, buyer_name):
        # 需要对现有的title进行精简
        # 原则1. 采购人的信息不需要在title中出现
        parsed_simple_title = self.title
        if buyer_name:
            # 1.1 去掉buyer的括号
            no_parenthesis_buyer_name = re.sub("\(.*?\)", "", buyer_name)
            no_parenthesis_buyer_name = re.sub("（.*?）", "", no_parenthesis_buyer_name)
            parsed_simple_title = self.title.replace(no_parenthesis_buyer_name, "")

            # 1.2 按照省市县区给buyer切分，将切分出来的内容在title中进行删除
            buyer_name_parts = re.split("[省市县区]", parsed_simple_title)
            for buyer_name_part in buyer_name_parts:
                for area_flag in ["省", "市", "县", "区"]:
                    need_delete = buyer_name_part + area_flag
                    parsed_simple_title = parsed_simple_title.replace(need_delete, "")
        # 原则2. 去掉表示地区的信息
        # 2.1 删除开头的省信息
        for p in PROVINCES + PROVINCES_ABBR:
            if parsed_simple_title.startswith(p):
                parsed_simple_title.replace(p, "")
        # 2.2 删除开头的市信息
        if parsed_simple_title[2] == "市" and is_all_chinese(parsed_simple_title[:2]):  # xx市
            parsed_simple_title = parsed_simple_title[3:]

        return parsed_simple_title

    def get_default_buyer_name(self):
        buyer_name = \
            self.parse_detail("采\s*购\s*人\s*信\s*息.*?名\s*称\s*(,*?)\n").strip(":").strip("：").strip() or \
            self.parse_detail("招\s*标\s*人\s*：(.*?)\n")



for idx, row in df.iterrows():
    gt_simple_title = row["项目名称"]
    gt_buyer_name = row["采购单位名称"]
    gt_budget = row["预算/限价（万元）"]
    gt_get_until_date = row["获取招标文件的截止日期"]
    source_title = row["原标题"]
    source_detail = row["详情信息"]

    baoxian_item = BaoxianItem(platform="", title=source_title, bid_type="")
    baoxian_item.set_detail(source_detail)

    pred_buyer_name = baoxian_item.get_default_buyer_name()
    pred_simple_title = baoxian_item.get_default_simple_title(pred_buyer_name)
    pred_budget = baoxian_item.get_default_budget()
    pred_get_bid_until = baoxian_item.get_default_get_bid_until()
    print()
