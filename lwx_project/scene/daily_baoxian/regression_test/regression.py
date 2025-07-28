import datetime
import re
import typing
from symbol import continue_stmt

import pandas as pd

from lwx_project.scene.daily_baoxian.const import REGRESSION_PATH, PROVINCES_ABBR, PROVINCES
from lwx_project.utils.strings import is_all_chinese, dedup_lines, is_any_digits

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
    def parse_detail(self, pattern, text=None, condition=None, extract_index=None, from_bottom_to_top=False) -> typing.Union[str, typing.Tuple[str]]:
        text = text or self.detail
        res = re.findall(pattern, text, re.DOTALL)
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

    def parse_detail_simple(self, pattern, text=None):
        text = text or self.detail
        res = re.findall(pattern, text, re.DOTALL)
        return res

    def get_default_budget(self):
        """
        预算金额：130.000000万元（采购包1：55.000000万元；采购包2：35.000000万元；采购包3：28.000000万元；采购包4：12.000000万元）

        """
        parsed_budget = self.parse_detail("预\s*算\s*金\s*额\s*(.*?\d.*?)\n").strip().replace(" ", "").replace(":", "").replace("：", "").strip() or \
            self.parse_detail("项\s*目\s*预\s*算\s*(.*?\d.*?)\n").strip().replace(" ", "").replace(":", "").replace("：", "").strip()
        # 处理括号进行备注的情况
        if "(" in parsed_budget:
            rest_content = parsed_budget.split("(")[1].replace("\n", "").strip()
            if rest_content.startswith("元") or rest_content.startswith("万元"):
                pass
            else:
                parsed_budget = parsed_budget.split("(")[0].strip()
        elif "（" in parsed_budget:
            rest_content = parsed_budget.split("（")[1].replace("\n", "").strip()
            if rest_content.startswith("元") or rest_content.startswith("万元"):
                pass
            else:
                parsed_budget = parsed_budget.split("（")[0].strip()

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
        """
三、获取招标文件

时间：自招标文件公告发布之日起5个工作日


三、获取公开招标文件的地点、方式、期限及售价

获取文件期限：2025年6月24日 至 2025年7月2日。

        """
        parsed_get_bid_until = self.parse_detail("获\s*取\s*招\s*标\s*文\s*件\s*.*?至(.*?)[日,，]", from_bottom_to_top=True).strip() or \
                               self.parse_detail("获\s*取\s*采\s*购\s*文\s*件\s*.*?至(.*?)[日,，]", from_bottom_to_top=True).strip() or \
                               self.parse_detail("获\s*取\s*竞\s*争\s*性\s*磋\s*商\s*文\s*件\s*.*?至(.*?)[日,，]", from_bottom_to_top=True).strip() or \
                               self.parse_detail("获\s*取\s*文\s*件\s*期\s*限\s*.*?至(.*?)[日,，]", from_bottom_to_top=True).strip() or \
                               self.parse_detail("获\s*取\s*.{1,8}文\s*件\s*.*?至(.*?)[日,，]", from_bottom_to_top=True).strip()

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
        """
1、采购人信息

采购人：重庆市九龙坡区残疾人联合会
        """
        return \
            self.parse_detail("采\s*购\s*人\s*信\s*息.*?名\s*称\s*(.*?)\n").strip(":").strip("：").strip() or \
            self.parse_detail("采\s*购\s*人\s*信\s*息\s*采\s*购\s*人\s*[:：]?\s*(.*?)\n").strip(":").strip("：").strip()


    def get_default_budget2(self):
        return self.get_default_budget()


class BidItem(BaoxianItem):

    def set_detail(self, detail):
        dedup_detail = dedup_lines(detail)
        super().set_detail(dedup_detail)
        return self

    def get_default_buyer_name(self):
        """
采购人信息
名称：
宣城职业技术学院


1.采购人信息
采购人名称：
福州市鼓楼区城市管理
和综合执法局
        """
        buyer_name = \
            self.parse_detail("招\s*标\s*人\s*[:：]\s*(.*?)\n").strip(":").strip("：").strip() or \
            self.parse_detail("采\s*购\s*人\s*信\s*息\s*[:：]?\s*名\s*称\s*[:：]?\s*(.*?)\n").strip(":").strip("：").strip() or \
            self.parse_detail("采\s*购\s*人\s*信\s*息\s*[:：]?.*?名\s*称\s*[:：]?\s*(.*?)地址").strip(":").strip("：").strip() or \
            self.parse_detail("招\s*标\s*人\s*为[:：]?\s*(.*?)[。，]").strip(":").strip("：").strip() or \
            self.parse_detail("采\s*购\s*人\s*为[:：]?\s*(.*?)[。，]").strip(":").strip("：").strip()
        buyer_name = buyer_name.replace("\n", "")
        return buyer_name

    def get_default_budget(self):
        """
预估金额：
 458.91
万元

项目资金来源为其他资金
 498240.00
元

3、本项目预算为：45万元/年。

预算金额：
40
万元

预算：
4 8
万元；

采购包预算金额（元）:280,000.00

1.1.4预估采购金额：100000元（含税）。

本项目最高限价为
3
0000
元，超过最高限价视为无效报价。


、预算资金：自筹资金
 18.32
 万元

最高限价为
3000
元
/
人
.
年
        """
        # 先尝试全文寻找
        parsed_budget = self.parse_detail("项\s*目\s*预\s*算\s*为\s*[:：]?\s*(.*?)\n")
        # 再尝试去掉换行符，整个拼到一起寻找
        if not parsed_budget:
            text = self.detail.replace("\n", "").replace(" ", "")
            parsed_budget = \
                self.parse_detail("预\s*估\s*金\s*额\s*[:：]?\s*(.*?\s*元)", text=text) or \
                self.parse_detail("预\s*估\s*采\s*购\s*金\s*额\s*[:：]?\s*(.*?\s*元)", text=text) or \
                self.parse_detail("资\s*金\s*来\s*源\s*为\s*其\s*他\s*资\s*金\s*[:：]?\s*(.*?\s*元)", text=text) or \
                self.parse_detail("预\s*算\s*金\s*额\s*[:：]?\s*(.*?\s*元)", text=text) or \
                self.parse_detail("预\s*算\s*.{1,10}\s*资\s*金\s*(.*?\s*元)", text=text) or \
                self.parse_detail("预\s*算\s*[:：]?\s*(.*?\s*元)", text=text) or \
                self.parse_detail("预\s*算\s*[:：]?\s*(.*?\s*)", text=text)
            if parsed_budget.startswith("约"):
                parsed_budget = parsed_budget[1:]
            if not is_any_digits(parsed_budget):
                return ""
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

    def get_default_budget2(self):
        """从定位到的关键字往后找"""
        budget = self.get_default_budget()
        if budget:
            return budget
        text = self.detail.replace("\n", "").replace(" ", "")
        keywords = ["项目预算", "预算金额", "预估金额", "资金来源", "预算", "最高限价"]
        budget = ""
        is_wan = False  # 是否是万元
        threshold = 20
        stop = False
        for keyword in keywords:
            if stop:
                break
            position = text.find(keyword)
            if position == -1:
                continue
            stop = True
            target_text = text[position: position + threshold + len(keyword)]
            for pointer_text in target_text:
                if pointer_text.isdigit() or pointer_text == "." or pointer_text == ",":
                    budget += pointer_text
                elif pointer_text == "万":
                    is_wan = True
        if stop:
            if is_wan:
                parsed_budget = str(float(budget.replace(",", "")))
            else:
                parsed_budget = str(float(budget.replace(",", "")) / 10000)
            return parsed_budget
        return ""

    def get_default_get_bid_until(self):
        """
三、获取采购文件
3.1
时间：
202
5
年
年
5
月
月
20
日至
202
4
年
年
5
月
月
2
7
日
日

竞争性磋商文件获取期限：
2025
年
04
月
23
日至
2025
年
04
月
29
日止

询比文件获取时间

获取询价文件时间、地点、方式：
1
、时间：即日起至
2025

获取采购文件
时间：
2025年0
4
月
29
日至
2025年0
5
月
06
日，每天上午
8:30至12:00，下午14:3
        """
        text = self.detail.replace("\n", "").replace("年年", "年").replace("月月", "月").replace("日日", "日")
        text = text.replace("到", "至")
        patterns = [
            r"文\s*件\s*获\s*取\s*期\s*限\s*[:：]?\s*.*?至(.*?)[日,，]",
            r"文\s*件\s*的\s*获\s*取\s*[:：]?\s*.*?至(.*?)[日,，]",
            r"文\s*件\s*获\s*取\s*时\s*间\s*[:：]?\s*.*?至(.*?)[日,，]",
            r"文\s*件\s*询\s*价\s*时\s*间\s*[:：]?\s*.*?至(.*?)[日,，]",
            r"询\s*价\s*文\s*件\s*时\s*间\s*[:：]?\s*.*?至(.*?)[日,，]",
            r"招\s*标\s*文\s*件\s*的\s*获\s*取\s*.*?至(.*?)[日,，]",
            r"获\s*取\s*采\s*购\s*文\s*件\s*时\s*间\s*.*?至(.*?)[日,，]",
        ]
        for pattern in patterns:
            get_bid_until = self.get_bid_until_with_re(pattern, text)
            if get_bid_until:
                return get_bid_until
        return ""


    def get_bid_until_with_re(self, pattern, text):
        parsed_get_bid_untils = self.parse_detail_simple(pattern, text=text)
        for parsed_get_bid_until in parsed_get_bid_untils:
            parsed_get_bid_until = parsed_get_bid_until.strip().replace(" ","")
            # 遍历寻找六个数字
            parsed_get_bid_until_ = ""
            parsed_get_bid_until_dig = ""
            for idx, c in enumerate(parsed_get_bid_until):
                parsed_get_bid_until_ += c
                if c.isdigit():
                    parsed_get_bid_until_dig += c
                if len(parsed_get_bid_until_dig) == 8:
                    break
                if idx > 20:
                    break
            try:
                date_obj = datetime.datetime.strptime(parsed_get_bid_until_dig, "%Y%m%d")
                return date_obj.strftime("%Y/%m/%d")
            except ValueError:
                pass
        return ""
        # get_bid_until = parsed_get_bid_until.replace("年", "/").replace("月", "/").replace("-", "/")
        # return get_bid_until

skip_idx = 62
# skip_idx = -1

problems = [
    8,  # 时间：自招标文件公告发布之日起5个工作日
    27,  # 时间：自招标文件公告发布之日起5个工作日
    28,  # 时间：自磋商文件公告发布之日起5个工作日
    # 正文没有招标人信息；
    12,
    17,
    18,
    19,
    41,

    # 无法找到预算
    32,  # gt直接是 '-'
    48,  # gt直接是 '-'

    63  # 最高限价为3000元/人.年   并不是一行，无法通过行进行判断。 gt给了 -
]

gt_problems = [
    # budget 错误
    8,  # budget 55只是其中一部分，总共130
    # url和gt不对应
    12,
    39,
    42,
    # 截止日期错误
    23,  # 截止日期应为 06-17，gt写的是06-16
]

report_problems = [
    12,  # 截止日期：2025-05-20 ～ 2024-05-27。  https://ctbpsp.com/#/bulletinDetail?uuid=1ceb253b-7564-43c8-a41f-0a45d9cfd414&inpvalue=%E6%84%8F%E5%A4%96&dataSource=1&tenderAgency=
]
for idx, row in df.iterrows():
    if idx <= skip_idx:
        continue
    gt_simple_title = row["项目名称"]
    gt_buyer_name = row["采购单位名称"]
    gt_budget = row["预算/限价（万元）"]
    gt_get_until_date = row["获取招标文件的截止日期"]
    source_title = row["原标题"]
    source_detail = row["详情信息"]
    platfrom = row["招采平台"]  # 中国政府采购网 ｜ 中国招标投标公共服务平台
    if platfrom == "中国政府采购网":
        baoxian_item = BaoxianItem(platform="", title=source_title, bid_type="")
    elif platfrom == "中国招标投标公共服务平台":
        baoxian_item = BidItem(platform="", title=source_title, bid_type="")
    else:
        continue

    baoxian_item.set_detail(source_detail)

    pred_buyer_name = baoxian_item.get_default_buyer_name()
    pred_simple_title = baoxian_item.get_default_simple_title(pred_buyer_name)
    pred_budget = baoxian_item.get_default_budget2()
    pred_get_bid_until = baoxian_item.get_default_get_bid_until()
    print()
