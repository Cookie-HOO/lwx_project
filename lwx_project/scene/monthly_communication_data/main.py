from lwx_project.scene.monthly_communication_data.cal_excel import detail_group_by
from lwx_project.scene.monthly_communication_data.check_excel import UploadInfo
from lwx_project.scene.monthly_communication_data.fill_excel import merge_caled_result


def cal_and_merge(upload_info: UploadInfo, code_rules_dict, after_one_done_callback):
    # 1. 计算所有的结果
    caled_result_list = detail_group_by(
        upload_info=upload_info,
        code_map=code_rules_dict,
        after_one_done_callback=after_one_done_callback,
    )

    # 2. 填充指定位置
    files_map = merge_caled_result(upload_info, caled_result_list)
    return files_map


if __name__ == '__main__':
    from lwx_project.scene.monthly_communication_data.const import DETAIL_PATH
    upload_info_ = UploadInfo(
        year=2025,
        upload_tuanxian_month_dict={1: DETAIL_PATH, 2: DETAIL_PATH, 3: DETAIL_PATH, 4: DETAIL_PATH, 5: DETAIL_PATH},
        important_month_dict={},
        officer_path=None,
    )

    result_list_ = detail_group_by(upload_info_, {
        "意外险": [],
        "健康险": [-7824, -7854],  # 后面可能动态变
        "寿险": [],
        "医疗基金": [+7824, +7854],  # 后面可能动态变
        "年金险": [],
    })

    merge_caled_result(upload_info_, result_list_)
    print()