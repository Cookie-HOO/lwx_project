import pandas as pd
from PyQt5.QtCore import pyqtSignal

from lwx_project.client.base import BaseWorker, WindowWithMainWorker
from lwx_project.scene.product_evaluation.main import before_run
from lwx_project.scene.product_evaluation.steps import data_preprocess, get_text, get_value, split_sheet

UPLOAD_REQUIRED_FILES = ["产品目录", "分行代理保险产品分险种销售情况统计表", "对应表", "上期保费"]  # 上传的文件必须要有


class Worker(BaseWorker):
    custom_set_term_match_signal = pyqtSignal(pd.DataFrame)  # 自定义信号

    def __init__(self):
        super().__init__()
        self.df_text = None
        self.df_value = None

    def my_run(self):
        stage = self.get_param("stage")  # self.equal_buffer_value.value()
        if stage == "stage1":  # 任务处在第一阶段，说明需要执行预处理和获取文本以及获取数值的操作
            before_run()  # 清理路径

            # 第一步：数据预处理：删除无效数据 + 匹配简称
            self.refresh_signal.emit("1. 数据预处理...")
            df = data_preprocess.main()

            # 第二步：获取文本
            self.refresh_signal.emit("2. 获取评价文本...")
            self.df_text = get_text.main(df)

            # 第三步：预处理期数
            self.refresh_signal.emit("3. 预处理期数...")
            self.df_value = get_value.main(df)
            self.custom_set_term_match_signal.emit(self.df_value)
        elif stage == "stage2":  # 任务处在第二阶段，说明用户指定完期数，并点击了继续执行
            # 第四步：excel拆分
            new_df_value = self.get_param("new_df_value")  # 需要window在获取用户修改的df_value后设置过来
            if self.df_text is None or new_df_value is None:
                return self.modal_signal.emit("error", msg="没有文本或者值")
            self.refresh_signal.emit("4. 拆分excel...")
            split_sheet.main(self.df_text, new_df_value)


class MyProductEvaluationClient(WindowWithMainWorker):
    # todo
    pass
