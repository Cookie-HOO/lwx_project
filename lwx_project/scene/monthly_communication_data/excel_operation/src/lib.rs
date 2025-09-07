mod excel_check;

use pyo3::prelude::*;


/// 定义 Python 模块
#[pymodule]
fn excel_operation(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // 这个 function 居然没有python 的 openpyxl 快，慢的有限，说明python的openpyxl优化的可以
    m.add_function(wrap_pyfunction!(excel_check::get_upload_type, m)?)?;
    m.add("__version__", "0.1.0")?;
    Ok(())
}
