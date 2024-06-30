import time

from PyQt5 import uic

from lwx_project.client.base import BaseWindow
from lwx_project.client.const import UI_PATH
from lwx_project.scene.activity_rate.const import DATA_TMP_PATH
from lwx_project.scene.activity_rate.steps import plot


class MyActivityRateClient(BaseWindow):
    def __init__(self):
        super(MyActivityRateClient, self).__init__()
        uic.loadUi(UI_PATH.format(file="activity_rate.ui"), self)  # 加载.ui文件
        self.setWindowTitle("活动率画图——By LWX")

        self.upload_table_button.clicked.connect(self.upload_and_plot)
        self.download_table_button.clicked.connect(lambda: self.download_zip_from_path(path=DATA_TMP_PATH, default_topic="活动率画图"))

    def upload_and_plot(self):
        self.clear_tmp_and_copy_important(tmp_path=DATA_TMP_PATH)
        tmp = self.upload_file_modal(copy_to=DATA_TMP_PATH)  # todo tmp_path作为BaseWindow的一个属性，上传、下载、初始化都需要
        if tmp is None:
            return
        start = time.time()
        plot.main()
        self.modal("info", title="success", msg=f"任务完成: {round(time.time()-start, 2)}秒")
