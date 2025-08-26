"""
招投标公共服务平台
https://ctbpsp.com/
"""
import datetime
import random
import time
import typing

from lwx_project.scene.daily_baoxian.vo import BaoxianItem, Worker
from lwx_project.utils.browser import init_local_browser, click_item, close_all_browser_instances
from playwright.sync_api import sync_playwright

from lwx_project.utils.strings import dedup_lines, is_any_digits

PLATFORM = "中国招标投标公共服务平台"

class BidInfoBaoxianItem(BaoxianItem):
    def __init__(self, title, tag_list):
        super().__init__(platform=PLATFORM, title=title, bid_type="招标公告")
        self._province, self._bid_type, _, _publish_date, *_ = tag_list

        # publish_date:
        _publish_date = _publish_date.replace("接收时间:", "").strip()
        self.publish_date = _publish_date

        _publish_date_obj = datetime.datetime.strptime(_publish_date, "%Y-%m-%d")
        self.publish_date_obj = _publish_date_obj

        # province: tag中找或者title中找
        self.province = BidInfoBaoxianItem.get_province_abbr_first(self._province) or \
                        BidInfoBaoxianItem.get_province_abbr_first(self.title)

    def set_url(self, url):
        self.url = url
        return self

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
            self.parse_detail("采\s*购\s*人\s*为[:：]?\s*(.*?)[。，]").strip(":").strip("：").strip() or \
            self.parse_detail("采\s*购\s*人\s*[:：]?\n\s*(.*?)[。，]", from_bottom_to_top=True).strip(":").strip("：").strip()
        buyer_name = buyer_name.replace("\n", "")
        return buyer_name

    def get_budget_with_re(self, pattern, text):
        origin_parsed_budget = self.parse_detail(pattern, text=text)
        parsed_budget = origin_parsed_budget
        if parsed_budget.startswith("约"):
            parsed_budget = parsed_budget[1:]
        if parsed_budget.startswith("为"):
            parsed_budget = parsed_budget[1:]
        parsed_budget = parsed_budget.replace("人民币", "")
        if not is_any_digits(parsed_budget):
            return ""
        try:
            if parsed_budget.endswith("万元") or parsed_budget.startswith("万元"):
                parsed_budget = parsed_budget.replace("万元", "").strip()
                parsed_budget = str(float(parsed_budget.replace(",", "")))
            elif parsed_budget.endswith("元") or (
                    len(parsed_budget) > 0 and parsed_budget[-1].isdigit()) or parsed_budget.startswith("元"):
                parsed_budget = parsed_budget.replace("元", "").strip()
                parsed_budget = str(float(parsed_budget.replace(",", "")) / 10000)
            else:
                pass
        except ValueError:
            if len(parsed_budget.split("\n")) > 2 and len(parsed_budget) > 50:  # 是一个长字符串
                return ""
            return origin_parsed_budget  # 解析失败返回最原始的内容
        return parsed_budget

    def get_default_budget_(self):
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


预算金额（最高限价）：
 206
元
/
人
/
年

项目控制价：
90
万元
/
年
        """
        # 先尝试全文寻找
        global_patterns = [
            r"项\s*目\s*预\s*算\s*为\s*[:：]?\s*(.*?)\n"
        ]
        patterns = [
            r"总\s*预\s*算\s*为\s*[:：]?\s*(.*?\s*元\s*/\s*人?\s*/?\s*年?)",
            r"招\s*标\s*控\s*制\s*价\s*[:：]?\s*(.*?\s*元\s*/\s*人?\s*/?\s*年?)",
            r"资\s*金\s*来\s*源\s*为\s*其\s*他\s*资\s*金\s*[:：]?\s*(.*?\s*元\s*/\s*人?\s*/?\s*年?)",
            r"资\s*金\s*来\s*源\s*为\s*自\s*筹\s*资\s*金\s*[:：]?\s*(.*?\s*元\s*/\s*人?\s*/?\s*年?)",
            r"项\s*目\s*采\s*购\s*预\s*算\s*为\s*[:：]?\s*(.*?\s*元\s*/\s*人?\s*/?\s*年?)",
            r"预\s*估\s*金\s*额\s*[:：]\s*(.*?\s*元\s*/\s*人?\s*/?\s*年?)",
            r"预\s*估\s*金\s*额\s*[:：]?\s*(.*?\s*元\s*/\s*人?\s*/?\s*年?)",
            r"预\s*估\s*采\s*购\s*金\s*额\s*[:：]\s*(.*?\s*元\s*/\s*人?\s*/?\s*年?)",
            r"预\s*估\s*采\s*购\s*金\s*额\s*[:：]?\s*(.*?\s*元\s*/\s*人?\s*/?\s*年?)",
            r"预\s*算\s*金\s*额\s*[:：]\s*(.*?\s*元\s*/\s*人?\s*/?\s*年?)",
            r"预\s*算\s*金\s*额\s*[:：]?\s*(.*?\s*元\s*/\s*人?\s*/?\s*年?)",
            r"预\s*算\s*.{1,10}\s*资\s*金\s*(.*?\s*元\s*/\s*人?\s*/?\s*年?)",
            r"预\s*算\s*[:：]?\s*(.*?\s*元\s*/\s*人?\s*/?\s*年?)",
            r"预\s*算\s*[:：]?\s*(.*?\s*)",
        ]


        for g_pattern in global_patterns:
            result = self.get_budget_with_re(g_pattern, self.detail)
            if result:
                return result

        text = self.detail.replace("\n", "").replace(" ", "")

        for pattern in patterns:
            result = self.get_budget_with_re(pattern, text)
            if result:
                return result
        return ""
        #
        # parsed_budget = self.parse_detail("项\s*目\s*预\s*算\s*为\s*[:：]?\s*(.*?)\n")
        # # 再尝试去掉换行符，整个拼到一起寻找
        # if not parsed_budget:
        #     text = self.detail.replace("\n", "").replace(" ", "")
        #     parsed_budget = \
        #         self.parse_detail("总\s*预\s*算\s*为\s*[:：]?\s*(.*?\s*元)", text=text) or \
        #         self.parse_detail("招\s*标\s*控\s*制\s*价\s*[:：]?\s*(.*?\s*元)", text=text) or \
        #         self.parse_detail("资\s*金\s*来\s*源\s*为\s*其\s*他\s*资\s*金\s*[:：]?\s*(.*?\s*元)", text=text) or \
        #         self.parse_detail("资\s*金\s*来\s*源\s*为\s*自\s*筹\s*资\s*金\s*[:：]?\s*(.*?\s*元)", text=text) or \
        #         self.parse_detail("预\s*估\s*金\s*额\s*[:：]\s*(.*?\s*元)", text=text) or \
        #         self.parse_detail("预\s*估\s*金\s*额\s*[:：]?\s*(.*?\s*元)", text=text) or \
        #         self.parse_detail("预\s*估\s*采\s*购\s*金\s*额\s*[:：]\s*(.*?\s*元)", text=text) or \
        #         self.parse_detail("预\s*估\s*采\s*购\s*金\s*额\s*[:：]?\s*(.*?\s*元)", text=text) or \
        #         self.parse_detail("预\s*算\s*金\s*额\s*[:：]\s*(.*?\s*元)", text=text) or \
        #         self.parse_detail("预\s*算\s*金\s*额\s*[:：]?\s*(.*?\s*元)", text=text) or \
        #         self.parse_detail("预\s*算\s*.{1,10}\s*资\s*金\s*(.*?\s*元)", text=text) or \
        #         self.parse_detail("预\s*算\s*[:：]?\s*(.*?\s*元)", text=text) or \
        #         self.parse_detail("预\s*算\s*[:：]?\s*(.*?\s*)", text=text)
        #     if parsed_budget.startswith("约"):
        #         parsed_budget = parsed_budget[1:]
        #     if parsed_budget.startswith("为"):
        #         parsed_budget = parsed_budget[1:]
        #     parsed_budget = parsed_budget.replace("人民币", "")
        #     if not is_any_digits(parsed_budget):
        #         return ""
        # try:
        #     if parsed_budget.endswith("万元") or parsed_budget.startswith("万元"):
        #         parsed_budget = parsed_budget.replace("万元", "").strip()
        #         parsed_budget = str(float(parsed_budget.replace(",", "")))
        #     elif parsed_budget.endswith("元") or (len(parsed_budget) > 0 and parsed_budget[-1].isdigit()) or parsed_budget.startswith("元"):
        #         parsed_budget = parsed_budget.replace("元", "").strip()
        #         parsed_budget = str(float(parsed_budget.replace(",", "")) / 10000)
        #     else:
        #         pass
        # except ValueError:
        #     pass
        # return parsed_budget

    def get_default_budget(self):
        """从定位到的关键字往后找"""
        budget = self.get_default_budget_()
        if budget:
            return budget
        text = self.detail.replace("\n", "").replace(" ", "")
        keywords = ["项目预算", "预算金额", "预估金额", "资金来源", "预算", "最高限价"]
        budget = ""
        is_wan = False  # 是否是万元
        is_precent = False
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
                    break
                elif pointer_text == "%":
                    is_precent = True
                    break
        if stop and budget and not is_precent:
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
            r"获\s*取\s*招\s*标\s*文\s*件\s*时\s*间\s*.*?至(.*?)[日,，]",
            r"获\s*取\s*文\s*件\s*时\s*间\s*.*?至(.*?)[日,，]",
            r"获\s*取\s*采\s*购\s*文\s*件\s*.*?至(.*?)[日,，]",
            r"获\s*取\s*招\s*标\s*文\s*件\s*.*?至(.*?)[日,，]",
            r"获\s*取\s*招\s*标\s*文\s*件\s*.*?至(.*?)[日,，]",
            r"采\s*购\s*文\s*件\s*的\s*提\s*供\s*期\s*限\s*.*?至(.*?)[日,，]",
            r"招\s*标\s*文\s*件\s*获\s*取\s*.*?至(.*?)[日,，]",
        ]
        for pattern in patterns:
            get_bid_until = self.get_bid_until_with_re(pattern, text)
            if get_bid_until:
                return get_bid_until
        return ""


class BidInfoWorker(Worker):
    URL = "https://ctbpsp.com/#/"

    CSS_LOGIN = "div#loginBtn"

    def __init__(self, platform):
        super().__init__(platform)
        self.baoxian_items: typing.List[BidInfoBaoxianItem] = []

    def check_env(self, page):
        page.goto(self.URL, wait_until="networkidle")
        if self.is_login(page):
            return self
        self.login(page)
        return self

    def go_for_baoxian_items_by_date(self, browser_context, page, start_date, end_date):
        """根据起止日期搜索符合条件的保险条目"""
        self.start_date = start_date
        self.end_date = end_date
        # 1 去页面
        page.goto(self.URL, wait_until="networkidle")
        # 2. 搜索内容
        # 搜索
        page.locator('input[id][name][type="text"]').fill("意外伤害")
        page.click("button.btns:text('搜索')")
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        # 选择类型
        page.get_by_placeholder("请选择业务类型").click()
        time.sleep(2)
        page.locator("ul > li > span:text('招标公告')").click()
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        return self

    def go_for_baoxian_details(
            self, browser_context, page,
            call_back_after_one_done: typing.Callable[[BaoxianItem], None] = None
    ):
        current_page = 1

        date_format = "%Y-%m-%d"
        start_date_obj = datetime.datetime.strptime(self.start_date, date_format)
        end_date_obj = datetime.datetime.strptime(self.end_date, date_format)
        while current_page <= self.MAX_PAGE_NUM:
            div_elements = page.locator("div.list_body > div.left > div.left_body")
            try:
                div_elements.first.wait_for(timeout=10000)  # 等待最多10秒
            except Exception:
                continue

            time.sleep(1)
            need_stop_go_to_next_page = False
            for i in range(div_elements.count()):
                baoxian_pointer = div_elements.nth(i)
                title = baoxian_pointer.locator("p").inner_text()  # title
                tags = baoxian_pointer.locator("div > span")
                tag_list = [tags.nth(i).inner_text() for i in range(tags.count())]  # 省市 ｜ 类型 ｜ xxx ｜ 时间

                baoxian_item = BidInfoBaoxianItem(title=title, tag_list=tag_list)
                if not BidInfoWorker.check_baoxian_item(baoxian_item):  # 如果不符合要求就跳过这一项
                    continue
                if baoxian_item.publish_date_obj < start_date_obj:
                    need_stop_go_to_next_page = True
                    break  # 当前日期已经在要求的开始日期之前，说明无需往后翻页
                elif start_date_obj <= baoxian_item.publish_date_obj <= end_date_obj:
                    pass
                else:
                    continue  # 跳过这一项

                # --- 新增：循环尝试打开真实页面，直到成功加载 ---
                detail_url = None
                final_page = None  # 用于保存成功加载的页面

                for _ in range(2):  # 最多尝试2次点击
                    with page.expect_popup() as popup_info:
                        baoxian_pointer.locator("p").click()  # 打开新页面

                    new_page = popup_info.value
                    new_page.wait_for_load_state("load", timeout=10000)

                    # 处理人机验证
                    print("等待人机验证")
                    while self.has_captcha(new_page):
                        time.sleep(2)
                    print("人机验证通过")

                    # 再次等待，避免验证后页面未加载
                    # new_page.wait_for_load_state("networkidle", timeout=10000)

                    # 检查是否加载了真实内容（非验证码页、非空白页）
                    current_url = new_page.url
                    if (
                            current_url
                            and "verify" not in current_url
                            and "security" not in current_url
                            and "captcha" not in current_url
                            and "vaptcha" not in current_url
                            and current_url != "about:blank"
                            and current_url != self.URL
                    ):
                        detail_url = current_url
                        final_page = new_page  # 保留这个有效的页面
                        break  # 成功打开，跳出重试
                    else:
                        new_page.close()  # 关闭无效页面
                        time.sleep(1)

                # --- 只有成功打开后，才提取内容 ---
                if final_page and detail_url:
                    # 此时页面已加载真实内容，再获取详情
                    page_error, content_text = BidInfoWorker.find_iframe_detail(final_page)
                    print(content_text)
                    final_page.close()  # 提取完成后关闭

                    baoxian_item.set_url(detail_url).set_detail(content_text)
                    baoxian_item.success = not page_error
                else:
                    # 所有尝试都失败
                    baoxian_item.set_url("").set_detail("")
                    baoxian_item.success = False

                if call_back_after_one_done is not None:
                    call_back_after_one_done(baoxian_item)
                # time.sleep(random.uniform(20, 30))

            if need_stop_go_to_next_page:
                break
            # 点击下一页
            page.click("a.next-link-item:text('下一页')")
            current_page += 1
            page.wait_for_load_state("networkidle")
            time.sleep(1)

        return self

    def retry_baoxian_items(
            self, browser_context, page, baoxian_items,
            call_back_after_one_start: typing.Callable[[int], None] = None,
            call_back_after_one_done: typing.Callable[[int, BaoxianItem], None] = None
    ):
        """重试所有失败的保险item"""
        self.check_env(page)
        for index, baoxian_item in enumerate(baoxian_items):
            if baoxian_item.success or baoxian_item.platform != PLATFORM:
                continue
            call_back_after_one_start(index)
            # 用一个新的页面
            new_page = browser_context.new_page()
            new_page.goto(baoxian_item.url, wait_until="networkidle")
            page_error, content_text = BidInfoWorker.find_iframe_detail(page)
            new_page.close()

            baoxian_item.success = not page_error
            baoxian_item.set_detail(content_text)
            call_back_after_one_done(index, baoxian_item)
            time.sleep(random.uniform(20, 30))

        return self

    def get_title_and_detail_by_url(self, browser_context, page, url) -> (str, str):
        """根据指定的url获取标题和详情"""
        new_page = browser_context.new_page()
        new_page.goto(url, wait_until="networkidle")
        page_error, content_text = BidInfoWorker.find_iframe_detail(new_page)
        title = new_page.locator("div.title_name")
        title_text = title.inner_text()
        new_page.close()
        time.sleep(random.uniform(20, 30))
        return title_text, content_text

    @staticmethod
    def find_iframe_detail(page):
        # 获取 iframe 的定位器
        try:
            page.locator("iframe.pdf-viewer").wait_for(timeout=5000)  # 等待最多5秒
        except Exception:
            return True, "获取失败"

        # 等待看是否报错
        iframe_locator = page.frame_locator("iframe.pdf-viewer")
        page_error = False
        try:
            iframe_locator.locator("span#errorMessage").first.wait_for(timeout=3000)  # 等待最多3秒
            content_text = iframe_locator.locator("span#errorMessage").inner_text()
            page_error = True
        except Exception:
            # 等待 iframe 内部的 #viewer 元素出现
            try:
                iframe_locator.locator("#viewer").first.wait_for(timeout=5000)  # 等待最多5秒
                content_text = iframe_locator.locator("#viewer").inner_text()
                if len(content_text) == 0:
                    page_error = True
            except Exception as e:
                content_text = "获取失败"
                page_error = True
                print(f"获取失败：{str(e)}")
        return page_error, content_text

    @staticmethod
    def is_login(page):
        login_button = page.locator(BidInfoWorker.CSS_LOGIN)
        return "登录信息定制开启更多服务" not in login_button.inner_text()

    @staticmethod
    def login(page):
        if BidInfoWorker.is_login(page):
            return
        # 关闭登陆提示
        click_item(page, "div.el-notification div.el-notification__closeBtn")
        # 点击登陆按钮
        click_item(page, BidInfoWorker.CSS_LOGIN)
        # 循环等待登陆
        while not BidInfoWorker.is_login(page):
            print("等待登陆")
            time.sleep(3)
        print("登陆成功")

    @staticmethod
    def has_captcha(page):
        try:
            page.locator("iframe").first.wait_for(state="attached", timeout=10000)
        except Exception:
            return False
        iframe_obj = page.locator("iframe")
        count = iframe_obj.count()
        for i in range(count):
            iframe_one_obj = iframe_obj.nth(i)
            if "ptcha" in (iframe_one_obj.get_attribute("src") or ""):
                return True
        return False



bid_info_worker = BidInfoWorker(PLATFORM)

if __name__ == '__main__':
    start_date_ = "2025-07-08"
    end_date_ = "2025-07-18"
    BidInfoWorker().init_browser_for_search().go_for_baoxian_items_by_date(start_date_, end_date_).go_for_baoxian_details([1])
