"""
中国政府采购网
https://www.ccgp.gov.cn

1. 输入意外，搜标题
2. 点击「公开招标」

对于结果的过滤
省市名称符合要求：以下22个之一
    北京、重庆、江苏、黑龙江、浙江、上海、湖南、安徽、河北、山东、江西、福建、厦门、广东、四川、辽宁、湖北、陕西、山西、宁波、广西、河南

"""
import random
import re
import time
import typing

from lwx_project.scene.daily_baoxian.vo import BaoxianItem, Worker

BID_TYPE_MAPPING = {
    "1": "公开招标",
    "10": "竞争性磋商",
}

PLATFORM = "中国政府采购网"

class GovBuyBaoxianItem(BaoxianItem):
    def __init__(self, title, url, bref, tags_text, bid_type):
        """
url:
http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202507/t20250708_24923229.htm

title:
杭锦旗医疗保障局城乡居民和职工无责意外保险(二次)招标公告

bref:
项目概况城乡居民和职工无责意外保险(二次)招标项目的潜在投标人应在内蒙古自治区政府采购网（政府采购云平台）获取招标文件，并于2025年07月30日09时00分（北京时间）前递交投标文件。一、项目基本情况项目编号：ES

tags_text:
2025.07.08 10:52:59 | 采购人：杭锦旗医疗保障局 | 代理机构：鄂尔多斯市公共资源交易中心杭锦旗分中心
公开招标公告 | 内蒙古 |
        """
        super().__init__(platform=PLATFORM, title=title, bid_type=bid_type)
        self.url = url
        self.bref = bref
        # self.tags_list = tags_text.split("|")
        self.tags_list = [i.strip() for i in re.split("[\n|]", tags_text)]
        self._publish_date, self._buyer_name, self._proxy, self._bid_type, self._province, *_ = self.tags_list
        self._buyer_name = self._buyer_name.replace("采购人：", "")
        self._proxy = self._proxy.replace("代理机构：", "")

        # 在摘要中就可以解析的内容
        # 省市：tag中有最准的省市，如果没有，从采购人中获取，如果再没有从title中获取
        self.province = self._province or \
                        GovBuyBaoxianItem.get_province_abbr_first(self._buyer_name) or \
                        GovBuyBaoxianItem.get_province_abbr_first(self.title)

    def parse_from_detail(self):
        # 采购人信息
        self.buyer_name = self._buyer_name or self.get_default_buyer_name()

        # 预算
        self.budget = self.get_default_budget()

        # 精简的标题
        self.simple_title = self.get_default_simple_title(self.buyer_name)

        # 截止日期
        self.get_bid_until = self.get_default_get_bid_until()
        return self


class GovBuyWorker(Worker):

    def __init__(self, platform):
        super().__init__(platform)
        self.baoxian_items: typing.List[GovBuyBaoxianItem] = []

    def go_for_baoxian_items_by_date(self, browser_context, page, start_date, end_date):
        """根据起止日期搜索符合条件的保险条目"""
        self.start_date = start_date
        self.end_date = end_date
        bid_types = ["1", "10"]
        for index, bid_type in enumerate(bid_types):  # 公开招标, 竞争性磋商
            baoxian_items = self._search(page, start_date=start_date, end_date=end_date, bid_type=bid_type)
            self.baoxian_items.extend(baoxian_items)
            if index != len(bid_types) - 1:
                time.sleep(random.uniform(2, 6))
        return self

    def go_for_baoxian_details(
            self, browser_context, page,
            call_back_after_one_done: typing.Callable[[BaoxianItem], None]=None
    ):
        """当用户确认保险项目后，获取项目详情内容"""
        for index, baoxian_item in enumerate(self.baoxian_items):
            if not self.check_baoxian_item(baoxian_item):
                continue
            page.goto(baoxian_item.url)
            detail = page.locator("div.vF_detail_content").inner_text()
            baoxian_item.set_detail(detail)
            if call_back_after_one_done:
                call_back_after_one_done(baoxian_item)
            if index != len(self.baoxian_items) - 1:
                time.sleep(random.uniform(2, 6))  # 等待1~3秒
        return self

    def get_title_and_detail_by_url(self, browser_context, page, url) -> (str, str):
        page = browser_context.new_page()
        # 等待某个元素出现
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_selector("div.vF_detail_content", timeout=10000)
        detail = page.locator("div.vF_detail_content").inner_text()
        title = page.locator("h2.tc").inner_text()
        time.sleep(random.uniform(2, 6))  # 等待1~3秒
        page.close()
        return title, detail

    @staticmethod
    def search_url(start_date: str, end_date: str, bid_type: str):
        start_date = start_date.replace('-', ':')
        end_date = end_date.replace('-', ':')
        search_dict = {
            "searchtype": "1",  # 公开招标
            "page_index": "1",
            "bidSort": "0",
            "buyerName": "",
            "projectId": "",
            "pinMu": "0",
            "bidType": bid_type,
            "dbselect": "bidx",
            "kw": "意外",
            "timeType": "6",  # 6自定义  3近一月  2近一周  1近三日  0今日
            "displayZone": "",
            "zoneId": "",
            "pppStatus": "0",
            "agentName": "",
            "start_time": start_date,  # "2025:07:08",  # 奇怪的格式
            "end_time": end_date,  # "2025:07:08",
        }
        base_url = "https://search.ccgp.gov.cn/bxsearch?"
        query_string = "&".join([f"{k}={v}" for k, v in search_dict.items()])
        url = base_url + query_string
        print("查询url: " + url)
        return url

    @staticmethod
    def find_all_items_within_one_page(page, bid_type: str) -> typing.List[GovBuyBaoxianItem]:
        bid_type_name = BID_TYPE_MAPPING.get(bid_type)
        res = []
        li_elements = page.locator("ul.vT-srch-result-list-bid > li")
        count = li_elements.count()
        print(f"{bid_type_name}: 当前页找到 {count} 个目标")
        # noinspection PyTypeChecker
        for i in range(count):
            li = li_elements.nth(i)

            a_text = li.locator("a").inner_text()  # title
            a_href = li.locator("a").get_attribute("href")  # url
            p_text = li.locator("p").inner_text()  # bref
            span_text = li.locator("span").inner_text()  # tags_text
            baoxian_item = GovBuyBaoxianItem(a_text, a_href, p_text, span_text, bid_type_name)
            if GovBuyWorker.check_baoxian_item(baoxian_item):
                res.append(baoxian_item)
                time.sleep(random.uniform(1, 3))
        return res

    @staticmethod
    def _search(page, start_date, end_date, bid_type: str) -> typing.List[GovBuyBaoxianItem]:
        """翻页
        start_date: 开始时间
        end_date: 结束时间
        bid_type: 1: 公开招标，10 竞争性磋商
        """
        res = []

        # page.goto("https://www.ccgp.gov.cn")
        page.goto(GovBuyWorker.search_url(start_date, end_date, bid_type))

        li_elements = page.locator("ul.vT-srch-result-list-bid > li")
        try:
            li_elements.first.wait_for(timeout=5000)
        except Exception:
            return res
        # page.wait_for_load_state("networkidle")

        current_page = 1
        next_button_count = 1
        while current_page <= GovBuyWorker.MAX_PAGE_NUM and next_button_count > 0:
            res.extend(GovBuyWorker.find_all_items_within_one_page(page, bid_type))
            next_button = page.locator("a.next")
            next_button_count = next_button.count()
            if next_button_count == 0:
                break
            # 需要下一页
            next_button.nth(0).click()
            li_elements = page.locator("ul.vT-srch-result-list-bid > li")
            try:
                li_elements.first.wait_for(timeout=5000)
            except Exception:
                return res
            # page.wait_for_load_state("networkidle")
            time.sleep(1)
            current_page += 1
        return res


gov_buy_worker = GovBuyWorker(platform=PLATFORM)


if __name__ == '__main__':
    start_date_ = "2025-07-08"
    end_date_ = "2025-07-18"
    gov_buy_worker.init_browser_for_search().go_for_baoxian_items_by_date(start_date_, end_date_).go_for_baoxian_details([1])

