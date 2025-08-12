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

    def parse_from_detail(self):
        """
        self.simple_title = "",
        self.buyer_name = "",
        self.budget = "",
        self.get_bid_until = "",
        """
        # 获取采购文件截止日期
        self.get_bid_until = self.get_default_get_bid_until()
        # 预算
        self.budget = self.get_default_budget()
        # 采购人
        self.buyer_name = self.get_default_buyer_name()
        # 精简的title（去掉采购人的信息，以及去掉省市信息）
        self.simple_title = self.get_default_simple_title(self.buyer_name)
        return self

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
                # 使用 expect_popup 来处理新标签页
                with page.expect_popup() as popup_info:
                    baoxian_pointer.locator("p").click()  # 这次点击会打开新页面

                # 切换到新建的页面
                new_page = popup_info.value
                detail_url = new_page.url
                new_page.wait_for_load_state("networkidle")
                while self.has_captcha(new_page):
                    print("等待人机验证")
                    time.sleep(2)
                print("人机验证通过")
                new_page.wait_for_load_state("networkidle")
                page_error, content_text = BidInfoWorker.find_iframe_detail(new_page)
                print(content_text)
                # 关闭打开的页面，回到原来的内容
                new_page.close()

                baoxian_item.set_url(detail_url).set_detail(content_text)
                baoxian_item.success = not page_error
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
            except Exception:
                content_text = "获取失败"
                page_error = True
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
