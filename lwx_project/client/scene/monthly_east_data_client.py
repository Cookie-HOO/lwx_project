import json
import os
import time

from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal

from lwx_project.client.base import BaseWorker, WindowWithMainWorker
from lwx_project.client.const import UI_PATH
from lwx_project.client.utils.list_widget import ListWidgetWrapper
from lwx_project.scene.monthly_east_data.cal_excel import CalExcelOneInfo
from lwx_project.scene.monthly_east_data.check_excel import check_excels
from lwx_project.scene.monthly_east_data.const import CONFIG_PATH, IMPORTANT_PATH, TEMPLATE_FILE_NAME_PREFIX, \
    TEMPLATE_FILE_NAME_SUFFIX
from lwx_project.scene.monthly_east_data.main import cal_and_merge
from lwx_project.utils.file import copy_file, open_file_or_folder
from lwx_project.utils.mail import send_mail
from lwx_project.utils.year_month_obj import YearMonth


class Worker(BaseWorker):
    custom_after_check_upload_signal = pyqtSignal(dict)
    custom_after_one_cal_signal = pyqtSignal(dict)
    custom_after_all_cal_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.once_clean = False
        self.sec_clean = False

    def my_run(self):
        stage = self.get_param("stage")
        if stage == "check_upload":  # {"核心团险数据": {}, "名称": "", "名称代码映射": ""}
            self.refresh_signal.emit("上传文件校验中...")
            file_path_list = self.get_param("file_path_list")
            is_success, error_msg, res = check_excels(file_path_list)

            self.custom_after_check_upload_signal.emit({
                "is_success": is_success,
                "error_msg": error_msg,
                "upload_file_path_map": res,
            })


        elif stage == "start_cal":
            self.refresh_signal.emit("计算中...")
            upload_file_path_map: dict = self.get_param("upload_file_path_map")
            target_year: str = self.get_param("target_year")
            omit_baoxian_code_list: list = self.get_param("omit_baoxian_code_list")

            cal_and_merge(
                upload_file_path_map,
                target_year,
                omit_baoxian_code_list,
                lambda cal_excel_one_info: self.custom_after_one_cal_signal.emit({
                    "cal_excel_one_info": cal_excel_one_info,
                })
            )
            self.refresh_signal.emit("✅计算完成")

            self.custom_after_all_cal_signal.emit({

            })


class MyMonthlyEastDataClient(WindowWithMainWorker):
    """
    """

    help_info_text = """
=========== 场景描述 ===========
上传核心团险数据表（必须）和关联方名称以及名称代码表（后两个可选）
核心团险数据表可以上传多个
程序会进行以下操作
1. 基础过滤：险种代码过滤 + 保全号不为空 + 团体保单过滤
2. 农行和其他关联方的数据
    农行：包含：中国农业银行的
    其他：在名单中的
2. 根据保险单号做groupby，计算其他列
3. 和important中之前计算的结果进行合并
每个月做一次

=========== Important文件 ===========
❗📗模板.xlsx
    保存内容模板，每次需要复制填数

❗📗其他关联方名称.xlsx
    上传的文件中如果有：只有一列的excel，会覆盖这个文件（没有列名）
    important路径下如果没有此文件，必须上传
    
❗📗其他关联方名称代码映射.xlsx
    上传的文件中如果有：只有两列的excel，会覆盖这个文件（没有列名）
    important路径下如果没有此文件，必须上传

❗🔧config.json
    使用方式：使用过程中的配置文件，自动记录，无需手动管理
        记录配置的需要忽略的险种代码

=========== 系统配置文件 ===========
❗🔧auth.json
    在data根路径下
    使用方式：{"liwenxuan_0112@126.com": "token"} 的方式进行记录

=========== 注意事项 ===========
1. 上传的文件中，除核心团险数据表外，其他excel文件没有列名
2. 自动进行区分：
    核心团险数据表：超过2列
    名称代码映射表：2列（没有列名，第一列是名称）
    名称表：1列（没有列名，第一列是名称）
3. 核心团险数据表如果是1个且不是1月，必须保证之前的月份做完了
4. 核心团险数据表如果是多个，必须保证是连续的月份，且是同一年的
    """

    release_info_text = """
v1.1.4 完成该场景
- 配置、上传，允许上传多个核心团险数据表
- 计算、融合
- 指定月份下载、发送
    """

    def __init__(self):
        """
        重要变量
            omit_baoxian_code_text：配置忽略险种代码规则的text
            target_year_text：默认是上个月对应的年份
            upload_button：上传文件按钮
                支持上传一个或多个核心团险数据excel，以及0个或1个内勤外勤人员统计
            cal_button：计算按钮
            download_file_button：下载文件按钮
                需要选定一个指定的月份，再下载
            send_file_button：发送文件按钮
            reset_button: 重置当前内容的button

            upload_info_text：上传后显示的汇总信息
                默认为空
            file_list：将计算完成的文件列出
        """
        super(MyMonthlyEastDataClient, self).__init__()
        uic.loadUi(UI_PATH.format(file="monthly_east_data.ui"), self)  # 加载.ui文件
        self.setWindowTitle("每月east数据汇总计算——By LWX")
        self.tip_loading = self.modal(level="loading", titile="加载中...", msg=None)
        # 初始化帮助信息
        self.help_info_button.clicked.connect(
            lambda: self.modal(level="info", msg=self.help_info_text, width=800, height=400))
        self.release_info_button.clicked.connect(lambda: self.modal(level="info", msg=self.release_info_text))

        # 设置默认的保险代码配置
        try:
            with open(CONFIG_PATH) as f:
                self.config = json.loads(f.read())
        except Exception:
            self.config = {"omit_baoxian_code": "7824,2801,7854"}
            with open(CONFIG_PATH, "w") as f:
                f.write(json.dumps(self.config))

        # 上传文件按钮
        self.upload_button.clicked.connect(self.upload_files_action)
        # 计算按钮
        self.cal_button.clicked.connect(self.cal_baoxian_action)
        # 下载文件按钮
        self.download_file_button.clicked.connect(self.download_file_action)
        # 发送邮件按钮
        self.send_file_button.clicked.connect(self.send_file_action)
        # 重置按钮
        self.reset_button.clicked.connect(self.reset_all_action)
        # 展示上传文件结果
        self.file_list_wrapper = ListWidgetWrapper(self.file_list).bind_double_click_func(self.double_click_to_open)

        # 初始化信息：会被重置
        self.file_list_wrapper.clear()  # 上传的list
        text = f"当前年份：--，汇总计算 --/--个月度数据，平均耗时 --s"
        self.upload_info_text.setText(text)

        self.upload_file_path_map = None  # 上传的结果 dict，{"核心团险数据": "", "名称": "", "名称代码映射": ""}

        self.done_f = []  # 已经计算好的文件，如果本次计算的有，那么会remove掉（上传后已打勾的文件）
        self.this_f = []  # 本次计算的文件（上传后待打勾的文件）

        # 记录过程信息
        self.done_num = 0
        self.start_run_time = None
        self.last_run_time = None


    def register_worker(self):
        return Worker()

    def upload_files_action(self):
        file_names = self.upload_file_modal(["Excel Files", "*.xls*"], multi=True)
        if not file_names:
            return

        params = {
            "stage": "check_upload",
            "file_path_list": file_names,
        }
        self.worker.add_params(params).start()

        # 增加loading tip
        self.tip_loading.set_titles(["上传文件校验.", "上传文件校验..", "上传文件校验..."]).show()

        pass

    def custom_after_check_upload(self, result):
        is_success = result.get("is_success")
        error_msg = result.get("error_msg")
        upload_file_path_map = result.get("upload_file_path_map")  # {"核心团险数据": {}, "名称": "", "名称代码映射": ""}
        core_dict = upload_file_path_map.get("核心团险数据")

        self.tip_loading.hide()

        # 校验是否通过
        if not is_success:
            self.modal(level="warn", msg=error_msg)
            return

        # 拼接展示的文件内容
        # 已经存在的内容
        file_list = [f for f in os.listdir(IMPORTANT_PATH) if f.startswith(TEMPLATE_FILE_NAME_PREFIX)]

        # 把本次计算的文件名也添加进去
        this_file_list = [TEMPLATE_FILE_NAME_PREFIX + i.str_with_only_number + TEMPLATE_FILE_NAME_SUFFIX for i in core_dict.keys()]

        # 融合：这次上传的会覆盖之前的算完的
        all_list = []
        for f in file_list + this_file_list:
            if f not in all_list:
                all_list.append(f)
        # 排序
        all_list.sort()
        self.done_f = [i for i in all_list if i not in this_file_list]
        self.this_f = [i for i in all_list if i in this_file_list]
        self.file_list_wrapper.fill_data_with_color(
            ["✅" + f for f in self.done_f] + self.this_f
        )
        self.upload_file_path_map = upload_file_path_map

        new_text = f"当前年份：{list(core_dict.keys())[0].year}，汇总计算 0/{len(core_dict)}个月度数据，平均耗时 --s"
        self.upload_info_text.setText(new_text)

    def cal_baoxian_action(self):
        if self.upload_file_path_map is None:
            self.modal(level="warn", msg="请先上传核心团险数据、名称表、名称代码映射表")
            return

        # 检查存在上个月的计算结果，逻辑如下
        """
        1. 找到上传的最小月，如果不是1月，那么上个月的必须做完了
        """
        year_month_obj: YearMonth = min(self.upload_file_path_map.get("核心团险数据").keys())
        last_year_month_obj = year_month_obj.sub_one_month()
        last_month_result = []
        if year_month_obj.month != 1:
            for file in self.file_list_wrapper.get_data_as_list():
                if last_year_month_obj.str_with_only_number in file:
                    last_month_result.append(file.lstrip("✅"))
                    break
            # 上面for的任务是寻找包含上个月内容的文件，这里的else就是如果找不到（没有触发break）
            # 或者理解为for循环中的那个if的break（所有都没有触发if之后会触发else）
            else:
                msg1 = f"要做{ year_month_obj.month}月的数据，没有找到{last_year_month_obj.month}月的计算结果"
                msg2 = f"请上传上个月份计算后的数据（手动添加到对应的important目录中）"
                msg3 = f"格式为: {TEMPLATE_FILE_NAME_PREFIX}{last_year_month_obj.str_with_only_number}{TEMPLATE_FILE_NAME_SUFFIX}"

                self.modal(level="warn", msg=msg1 + "\n\n" + msg2 + "\n\n" + msg3)
                return
        else: # 是一月，不需要上月
            last_month_result.append("")

        # 发起计算任务
        self.start_run_time = time.time()
        self.last_run_time = time.time()
        params = {
            "stage": "start_cal",
            "upload_file_path_map": self.upload_file_path_map,
            "target_year": year_month_obj.year,
            "omit_baoxian_code_list": [i.strip() for i in self.omit_baoxian_code_text.text().split(",")],
        }
        self.worker.add_params(params).start()

        # 保存当前的配置：忽略的保险代码
        self.config["omit_baoxian_code"] = self.omit_baoxian_code_text.text()
        with open(CONFIG_PATH, "w") as f:
            f.write(json.dumps(self.config))

        # 设置展示：run
        for ind, file in enumerate(self.file_list_wrapper.get_data_as_list()):
            if year_month_obj.str_with_only_number in file:
                self.file_list_wrapper.set_text_by_index(ind, "🏃" + file)

        # 增加loading tip
        self.tip_loading.set_titles(["计算.", "计算..", "计算..."]).show()

    def custom_after_one_cal(self, result):
        cal_excel_one_info: CalExcelOneInfo = result.get("cal_excel_one_info")
        target_file_name = cal_excel_one_info.target_file_name
        year_month_obj = cal_excel_one_info.year_month_obj
        self.done_num += 1

        # 修改文字
        all_f: list = self.done_f + self.this_f
        # done
        index = all_f.index(target_file_name)
        self.file_list_wrapper.set_text_by_index(
            index,
            "✅" + target_file_name + f"\t{round(time.time()-self.last_run_time, 2)}s\t当月abc&非abc：{cal_excel_one_info.cur_abc_num} & {cal_excel_one_info.cur_other_num}\t截止当月abc&非abc：{cal_excel_one_info.max_abc_num} & {cal_excel_one_info.max_other_num}"
        )

        # run
        t = self.file_list_wrapper.get_text_by_index(index+1)
        if t is not None:
            self.file_list_wrapper.set_text_by_index(index+1, "🏃" + t)

        # 更新时间
        need_cal = len(self.this_f)
        new_text = f"当前年份：{year_month_obj.str_with_dash}，汇总计算 {self.done_num}/{need_cal}个月度数据，平均耗时 {round((time.time()-self.start_run_time)/self.done_num, 2)}s"
        self.upload_info_text.setText(new_text)
        self.last_run_time = time.time()

        pass

    def custom_after_all_cal(self, result):
        self.tip_loading.hide()

    def download_file_action(self):
        if not self.file_list_wrapper.get_data_as_list():
            self.modal(level="warn", msg="请先计算")
            return
        selected = self.file_list_wrapper.get_selected_text()
        if selected:
            file = selected[0]
            if "✅" not in file:
                self.modal(level="warn", msg="文件未计算完成，无法下载")
                return
        else:
            file = self.file_list_wrapper.get_text_by_index(-1)
        file = file.strip("✅").split("\t")[0].strip()
        file_path = os.path.join(IMPORTANT_PATH, file)
        target_file_path = self.download_file_modal(file)
        if not target_file_path:
            return
        copy_file(file_path, target_file_path)
        self.modal(level="info", msg="✅下载成功")

    def send_file_action(self):
        if not self.file_list_wrapper.get_data_as_list():
            self.modal(level="warn", msg="请先计算")
            return
        selected = self.file_list_wrapper.get_selected_text()
        if selected:
            file = selected[0]
            if "✅" not in file:
                self.modal(level="warn", msg="文件未计算完成，无法发送")
                return
        else:
            file = self.file_list_wrapper.get_text_by_index(-1)
        file = file.strip("✅").split("\t")[0].strip()
        file_path = os.path.join(IMPORTANT_PATH, file)

        check_yes = self.modal(level="check_yes", msg=f"即将发送：{file}", default="no")
        if not check_yes:
            return
        # 发送文件
        from_email = "liwenxuan_0112@126.com"
        to_email = "liwenxuanrs@abchina.com"
        subject = file
        attachments = [file_path]
        send_mail(
            from_email=from_email,
            to_email=to_email,
            subject=subject,
            body="",
            attachments=attachments
        )
        self.modal(level="tip", count_down=2, msg="✅发送成功(2秒后关闭)")

    def double_click_to_open(self, file):
        if not file.startswith("✅"):
            self.modal(level="warn", msg="请等待执行完成后再打开")
            return
        file = file.strip("✅").split("\t")[0].strip()
        file_path = os.path.join(IMPORTANT_PATH, file)
        open_file_or_folder(file_path)

    def reset_all_action(self):
        self.file_list_wrapper.clear()  # 上传的list
        # 初始化信息：会被重置
        text = f"当前年份：--，汇总计算 --/--个月度数据，平均耗时 --s"
        self.upload_info_text.setText(text)

        self.upload_file_path_map = None  # 上传的结果 dict，{"核心团险数据": "", "名称": "", "名称代码映射": ""}

        self.done_f = []  # 已经计算好的文件，如果本次计算的有，那么会remove掉（上传后已打勾的文件）
        self.this_f = []  # 本次计算的文件（上传后待打勾的文件）

        # 记录过程信息
        self.done_num = 0
        self.start_run_time = None
        self.last_run_time = None
        self.modal("info", title="Success", msg="重置成功")

