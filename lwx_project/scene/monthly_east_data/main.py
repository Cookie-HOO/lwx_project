from lwx_project.scene.monthly_east_data.cal_excel import baoxian_order_code_groupby
from lwx_project.utils.file import copy_file


def cal_and_merge(last_month_template_path: str, upload_file_path_map: dict, target_year: str, target_file_path: str, omit_baoxian_code_list: list):
    """
    last_month_template_path: str
        上个月的模板文件路径
    upload_file_path_map: dict
        上传的文件路径映射，{"核心团险数据": "", "名称": "", "名称代码映射": ""}
    target_year: str
        目标年份
    target_file_path:
        目标文件名(拷贝上月的模板文件出来的）
    omit_baoxian_code_list: list
        忽略的保险代码列表
    """
    # 1. 计算这个月的汇总数据
    path = upload_file_path_map.get("核心团险数据")
    name_path = upload_file_path_map.get("名称")
    name_code_path = upload_file_path_map.get("名称代码映射")
    df = baoxian_order_code_groupby(
        path=path,
        last_month_template_path=last_month_template_path,
        omit_baoxian_code_list=omit_baoxian_code_list,
        year=target_year,
        connection_name_path=name_path,
        connection_name_code_path=name_code_path,
    )

    # 2. 在新的文件中先删除，再填充
    # 基于模板复制
    copy_file(last_month_template_path, target_file_path)


if __name__ == '__main__':
    # TODO
    last_month_template_path = ""
    upload_file_path_map = {
        "核心团险数据": "",
        "名称": "",
        "名称代码映射": "",
    }
    target_year = "2025"
    target_file_path = ""
    omit_baoxian_code_list = []

    cal_and_merge(
        last_month_template_path,
        upload_file_path_map,
        target_year,
        target_file_path,
        omit_baoxian_code_list,
    )