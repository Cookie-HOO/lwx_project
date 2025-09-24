import datetime
import re
import time
import typing

from lwx_project.scene.daily_baoxian.area_data import find_city_for_buyer_name
from lwx_project.scene.daily_baoxian.const import PROVINCES_ABBR, PROVINCES
from lwx_project.utils.browser import init_local_browser, close_all_browser_instances

from playwright.sync_api import sync_playwright

from lwx_project.utils.date import add_days_skip_weekends
from lwx_project.utils.strings import is_all_chinese, can_convert2float


class BaoxianItem:
    def __init__(self, platform, title, bid_type):
        self.platform = platform
        self.title = title
        self.province = ""
        self.url = ""
        self.detail = ""
        self.publish_date = ""

        # check时进行校验
        self.default_available = True
        self.not_available_reason = ""

        # 需要下载的内容
        self.simple_title: str = ""
        self.bid_type: str = bid_type
        self.buyer_name: str = ""
        self.budget: str = ""
        self.get_bid_until: str = ""

        self.success = True

        self._buyer_name = ""

        self.key_city = ""  # 地级市，有时buyer_name中写的很细，不知道是哪里的，所以解析出地级市补充到buyer_name中

    @staticmethod
    def get_province_abbr_first(content):
        for p in PROVINCES_ABBR + PROVINCES:  # 先找简称
            if content.startswith(p):
                return p
        return ""

    def parse_from_detail(self):
        # 采购人信息
        self.buyer_name = self._buyer_name or self.get_default_buyer_name()

        # 预算
        self.budget = self.get_default_budget()

        # 精简的标题
        self.simple_title = self.get_default_simple_title(self.buyer_name) or self.title

        # 截止日期
        self.get_bid_until = self.get_default_get_bid_until()
        return self

    def set_detail(self, detail):
        # 赋值
        self.detail = detail
        # 解析内容
        self.parse_from_detail()
        # 增加地级市
        province, key_city = find_city_for_buyer_name(self.province,self.buyer_name,self.title)
        self.key_city = key_city
        self.province = self.province or province

        # 项目流标
        if self.detail.replace("\n", "").replace(" ", "") == "经评审，无有效投标人，本项目流标。":
            self.success = False
            self.not_available_reason = "项目流标"
            self.buyer_name = "项目流标"
            self.get_bid_until = "项目流标"
            self.budget = "项目流标"
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


    def get_budget_with_re(self, pattern, text):
        origin_parsed_budget = self.parse_detail(pattern, text=text).strip()
        parsed_budget = origin_parsed_budget.replace(" ", "").replace(":", "").replace("：", "").strip()
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

        parsed_budget = parsed_budget.replace("(", "").replace(")", "").replace("（", "").replace("）", "").replace(":","").replace("：", "").strip()
        parsed_budget = parsed_budget.replace("人民币", "").strip()
        try:
            if parsed_budget.endswith("万元") or parsed_budget.startswith("万元"):
                parsed_budget = parsed_budget.replace("万元", "").strip()
                parsed_budget = str(float(parsed_budget.replace(",", "")))
            elif parsed_budget.endswith("元") or (len(parsed_budget) > 0 and parsed_budget[-1].isdigit()) or parsed_budget.startswith("元"):
                parsed_budget = parsed_budget.replace("元", "").strip()
                parsed_budget = str(round(float(parsed_budget.replace(",", "")) / 10000, 4))  # noqa
            else:
                pass
        except ValueError:
            if len(parsed_budget.split("\n")) > 2 and len(parsed_budget) > 50:  # 是一个长字符串
                return origin_parsed_budget
            return origin_parsed_budget  # 解析失败返回最原始的内容
        return parsed_budget


    def get_default_budget(self):
        """
        预算金额：130.000000万元（采购包1：55.000000万元；采购包2：35.000000万元；采购包3：28.000000万元；采购包4：12.000000万元）

        """
        patterns = [
            "预\s*算\s*金\s*额\s*[:：]\s*(.*?\d.*?)[\n。，]",
            "项\s*目\s*预\s*算\s*[:：]\s*(.*?\d.*?)[\n。，]",
            "预\s*算\s*金\s*额\s*为?\s*(.*?\d.*?)[\n。，]",
            "项\s*目\s*预\s*算\s*为?\s*(.*?\d.*?)[\n。，]",
            "预\s*算\s*金\s*额\s*(.*?\d.*?)[\n。，]",
            "项\s*目\s*预\s*算\s*(.*?\d.*?)[\n。，]",
            "采\s*购\s*预\s*算\s*价\s*为?\s*(.*?\d.*?)[\n。，]"
        ]
        for pattern in patterns:
            # 对于 gov 网站来说，模式相对固定，但是找到的内容可能有冗余，需要进一步操作
            result = self.get_budget_with_re(pattern, text=self.detail)
            if result:
                if can_convert2float(result):
                    return result
                num = self.find_budget_by_number([""], result)
                if num:
                    return num
        return ""

    def find_budget_by_number(self, keywords, text):
        budget = ""
        is_wan = False  # 是否是万元
        stop = False

        threshold = 20
        while_key_words = keywords[:]
        while while_key_words and not stop:
            # 重新刷新纪录的信息
            budget = ""
            is_wan = False  # 是否是万元
            stop = False

            keyword = while_key_words.pop(0)
            position = text.find(keyword)
            if position == -1:
                continue
            target_text = text[position: position + threshold + len(keyword)]
            for pointer_text in target_text:
                if pointer_text.isdigit() or pointer_text == "." or pointer_text == ",":
                    budget += pointer_text
                elif pointer_text == "万":
                    is_wan = True
                    stop = True
                    break
                elif pointer_text == "%":  # 一般是 资金来源：100%自有资金
                    break
                elif pointer_text == "元":
                    is_wan = False
                    stop = True
                    break
        if stop and budget:
            if is_wan:
                parsed_budget = str(float(budget.replace(",", "")))
            else:
                parsed_budget = str(round(float(budget.replace(",", "")) / 10000, 4))
            return parsed_budget
        return ""

    def get_default_get_bid_until(self):
        """
三、获取招标文件

时间：自招标文件公告发布之日起5个工作日


三、获取公开招标文件的地点、方式、期限及售价

获取文件期限：2025年6月24日 至 2025年7月2日。

        """
        # text = self.detail.replace("\n", "").replace("年年", "年").replace("月月", "月").replace("日日", "日")
        text = self.detail.replace("到", "至")
        patterns1 = [
            "获\s*取",
        ]
        patterns2 = [
            r"招\s*标\s*文\s*件",
            r"采\s*购\s*文\s*件",
            r"竞\s*争\s*性\s*磋\s*商\s*文\s*件",
            r"磋\s*商\s*文\s*件",
            r"文\s*件\s*期\s*限",
            r".{1,8}文\s*件",
        ]
        patterns3 = [
            ".{1,30}?至(.*?)[日,，]",
        ]
        for pattern1 in patterns1:
            for pattern2 in patterns2:
                for pattern3 in patterns3:
                    pattern_makeup1 = "\s*".join([pattern1, pattern2, pattern3])
                    get_bid_until = self.get_bid_until_with_re(pattern_makeup1, text)
                    if get_bid_until:
                        return get_bid_until

                    pattern_makeup2 = "\s*".join([pattern2, pattern1, pattern3])
                    get_bid_until = self.get_bid_until_with_re(pattern_makeup2, text)
                    if get_bid_until:
                        return get_bid_until

        # 特殊的写法：时间：自招标文件公告发布之日起5个工作日 ｜ 时间：自磋商文件公告发布之日起5个工作日 ｜ 时间：自本文件公告发布之日起5个工作日
        patterns1 = [
            "获\s*取\s*招\s*标\s*文\s*件\s*",
            "获\s*取\s*采\s*购\s*文\s*件\s*",
            "获\s*取\s*文\s*件\s*期\s*限\s*",
        ]
        patterns2 = [
            "",
            "时间[:：]",
        ]
        patterns3 = [
            "自招标文件公告发布之日起(.*?)个工作日",
            "自磋商文件公告发布之日起(.*?)个工作日",
            "自本文件公告发布之日起(.*?)个工作日",
        ]
        for pattern1 in patterns1:
            for pattern2 in patterns2:
                for pattern3 in patterns3:
                    pattern = pattern1 + pattern2 + pattern3
                    days = self.parse_detail(pattern, text=self.detail.replace("\n", ""))
                    if days.isdigit():
                        days_int = int(days)
                        until_date = add_days_skip_weekends(self.publish_date, days_int)
                        return until_date.replace("-", "/")

        return ""


        # parsed_get_bid_until = self.parse_detail("获\s*取\s*招\s*标\s*文\s*件\s*.*?至(.*?)[日,，]", from_bottom_to_top=True).strip() or \
        #                        self.parse_detail("获\s*取\s*采\s*购\s*文\s*件\s*.*?至(.*?)[日,，]", from_bottom_to_top=True).strip() or \
        #                        self.parse_detail("获\s*取\s*竞\s*争\s*性\s*磋\s*商\s*文\s*件\s*.*?至(.*?)[日,，]", from_bottom_to_top=True).strip() or \
        #                        self.parse_detail("获\s*取\s*文\s*件\s*期\s*限\s*.*?至(.*?)[日,，]", from_bottom_to_top=True).strip() or \
        #                        self.parse_detail("获\s*取\s*.{1,8}文\s*件\s*.*?至(.*?)[日,，]", from_bottom_to_top=True).strip()
        #
        # get_bid_until = parsed_get_bid_until.replace("年", "/").replace("月", "/").replace("-", "/")
        # return get_bid_until

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
        if len(parsed_simple_title) > 2 and parsed_simple_title[2] == "市" and is_all_chinese(parsed_simple_title[:2]):  # xx市
            parsed_simple_title = parsed_simple_title[3:]

        # 3. 兜底处理
        # 3.1 如果处理完后，是已「）」右括号开头，需要去掉
        if parsed_simple_title.startswith("）"):
            parsed_simple_title = parsed_simple_title[1:]
        return parsed_simple_title

    def get_default_buyer_name(self):
        """
1、采购人信息

采购人：重庆市九龙坡区残疾人联合会
        """
        return \
            self.parse_detail("采\s*购\s*人\s*信\s*息.*?名\s*称\s*(.*?)\n").strip(":").strip("：").strip() or \
            self.parse_detail("采\s*购\s*人\s*信\s*息\s*采\s*购\s*人\s*[:：]?\s*(.*?)\n").strip(":").strip("：").strip() or \
            self.parse_detail("采\s*购\s*人\s*[:：]?\s*(.*?)\n", from_bottom_to_top=True).strip(":").strip("：").strip()


class Worker:
    MAX_PAGE_NUM = 10  # 最多n页，不考虑n+1页

    def __init__(self, platform, call_back_after_one_done: typing.Callable[[BaoxianItem], None]=None):
        self.platform = platform
        self.start_date = ""
        self.end_date = ""

    def check_env(self, page):
        """初始化进行登陆态检查"""
        return self

    def go_for_baoxian_items_by_date(self, browser_context, page, start_date, end_date):
        """根据起止日期搜索符合条件的保险条目"""
        return self

    def go_for_baoxian_details(
            self, browser_context, page,
            call_back_after_one_done: typing.Callable[[BaoxianItem], None]=None
    ):
        """当用户确认保险项目后，获取项目详情内容"""
        return self

    def retry_baoxian_items(
            self, browser_context, page, baoxian_items,
            call_back_after_one_start: typing.Callable[[int], None] = None,
            call_back_after_one_done: typing.Callable[[int, BaoxianItem], None] = None
    ):
        """重试所有失败的保险item"""
        return self

    @staticmethod
    def check_baoxian_item(baoxian_item: BaoxianItem) -> bool:
        """
        检查所有条目，给符合条件的设置属性 default_available
        1. 省市名称符合要求：以下22个之一
            北京、重庆、江苏、黑龙江、浙江、上海、湖南、安徽、河北、山东、江西、福建、厦门、广东、四川、辽宁、湖北、陕西、山西、宁波、广西、河南、大连、青岛、深圳
        2. 标题中不能含有「责任险」、「第三者意外险」 字样
        """
        target_province_list = "北京、重庆、江苏、黑龙江、浙江、上海、湖南、安徽、河北、山东、江西、福建、厦门、广东、四川、辽宁、湖北、陕西、山西、宁波、广西、河南、大连、青岛、深圳"
        omit_baoxian_list = ["责任险", "责任保险", "第三者意外险"]
        # 1. 省市名称符合条件
        if baoxian_item.province not in target_province_list:
            baoxian_item.default_available = False
            baoxian_item.not_available_reason = f"{baoxian_item.province} 不属于25个目标省市之一"
            return False

        # 2. 没有出现特殊信息
        for omit_baoxian in omit_baoxian_list:
            if omit_baoxian in baoxian_item.title:
                baoxian_item.default_available = False
                baoxian_item.not_available_reason = f"标题包含「{omit_baoxian}」"
                return False

        baoxian_item.default_available = True
        return True

    def get_title_and_detail_by_url(self, browser_context, page, url) -> (str, str):
        """根据指定的url获取标题和详情"""
        return "", ""


class WorkerManager:
    def __init__(self):
        self.workers: typing.List[Worker] = []
        self.p_ins = None
        self.p = None
        self.browser_context = None
        self.page = None
        self.running = None

    def add_worker(self, worker: Worker):
        self.workers.append(worker)

    def init_browser(self, browser_bin_path):
        self.p_ins = sync_playwright()
        self.p = self.p_ins.__enter__()
        result =  init_local_browser(
            self.p, browser_bin_path, headless=False
        )
        while result is None:
            time.sleep(1)
            result = init_local_browser(
                self.p, browser_bin_path, headless=False
            )
        self.browser_context, self.page = result
        return self

    def close_browser(self):
        if self.p_ins is not None:
            self.p_ins.__exit__(None, None, None)

        self.p_ins = None
        self.p = None
        self.browser_context = None
        self.page = None
        return self

    def check_env(self):
        for worker in self.workers:
            worker.check_env(self.page)
        return self

    def search_baoxian_by_date(
            self, start_date, end_date,
            call_back_after_one_done: typing.Callable[[BaoxianItem], None]
    ):
        self.running = True
        for worker in self.workers:
            worker \
                .go_for_baoxian_items_by_date(browser_context=self.browser_context, page=self.page, start_date=start_date, end_date=end_date) \
                .go_for_baoxian_details(browser_context=self.browser_context, page=self.page, call_back_after_one_done=call_back_after_one_done)

        self.running = False
        return self

    def retry_baoxian_items(
            self,
            baoxian_items: typing.List[BaoxianItem],
            call_back_after_one_start: typing.Callable[[int], None],
            call_back_after_one_done: typing.Callable[[int, BaoxianItem], None],
    ):
        for worker in self.workers:
            worker.retry_baoxian_items(
                browser_context=self.browser_context,
                page=self.page,
                baoxian_items=baoxian_items,
                call_back_after_one_start=call_back_after_one_start,
                call_back_after_one_done=call_back_after_one_done
            )
    def get_for_title_and_detail(self, platform, url) -> (str, str):
        workers = [i for i in self.workers if i.platform == platform]
        if not workers:
            return "", ""
        worker = workers[0]
        return worker.get_title_and_detail_by_url(
            browser_context=self.browser_context,
            page=self.page,
            url=url
        )

worker_manager = WorkerManager()
