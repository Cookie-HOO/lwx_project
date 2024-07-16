from lwx_project.utils.excel_style import ExcelStyleValue
from lwx_project.utils.time_obj import TimeObj


class BenefitAchieve:
    def __init__(self, overall_excel_wrapper: ExcelStyleValue, report_time_obj: TimeObj):
        self.overall_excel_wrapper = overall_excel_wrapper
        self.report_time_obj = report_time_obj

    @staticmethod
    def check() -> (bool, str):
        pass

    def do(self):
        pass
