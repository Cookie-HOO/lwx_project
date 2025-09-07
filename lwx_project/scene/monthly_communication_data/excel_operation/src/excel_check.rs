use calamine::{Reader, Xlsx, open_workbook, DataType};
use pyo3::prelude::*;
use std::path::Path;

const UPLOAD_TYPE_TUANXIAN: &str = "tuanxian";
const UPLOAD_TYPE_OFFICER: &str = "officer";

#[pyfunction]
pub fn get_upload_type(file_path: &str) -> PyResult<String> {
    let path = Path::new(file_path);

    // 检查文件是否存在
    if !path.exists() {
        return Err(pyo3::exceptions::PyFileNotFoundError::new_err(format!(
            "文件不存在: {}", file_path
        )));
    }

    // 打开 .xlsx 文件
    let mut workbook: Xlsx<_> = open_workbook(path)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("无法打开 Excel 文件: {}", e)))?;

    // 获取第一个 sheet 名
    let sheet_name = workbook
        .sheet_names()
        .get(0)
        .ok_or_else(|| pyo3::exceptions::PyValueError::new_err("Excel 文件没有工作表"))?.clone();

    // 获取 sheet 数据
    let range = workbook
        .worksheet_range(&sheet_name)
        .ok_or_else(|| pyo3::exceptions::PyValueError::new_err(format!(
            "无法读取工作表 '{}': 未找到数据",
            sheet_name
        )))?
        .map_err(|_e| pyo3::exceptions::PyValueError::new_err(format!(
            "无法读取工作表 '{}': 未找到数据",
            sheet_name
        )))?;

    // 获取第一行（列名）
    let header_row = range.rows().next().ok_or_else(|| {
        pyo3::exceptions::PyValueError::new_err("Excel 文件为空，无数据行")
    })?;

    // 检查是否有「机构代码」
    for cell in header_row {
        if let DataType::String(s) = cell {
            if s.contains("机构代码") {
                return Ok(UPLOAD_TYPE_TUANXIAN.to_string());
            }
        }
    }

    Ok(UPLOAD_TYPE_OFFICER.to_string())
}