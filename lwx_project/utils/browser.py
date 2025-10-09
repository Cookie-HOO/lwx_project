import time
import subprocess
import platform
import os

from lwx_project.const import ALL_DATA_PATH

user_data_dir = os.path.join(ALL_DATA_PATH, ".browser_data")
if not os.path.exists(user_data_dir):
    os.makedirs(user_data_dir)

def init_local_browser(p, browser_bin_path, headless=False, port=None, user_data_dir_suffix=None):
    """
    关闭所有现有Chrome实例，然后启动一个新的实例并连接。
    支持 Windows 和 macOS。
    :param p: Playwright 实例
    :param browser_bin_path: 浏览器的可执行文件路径
    :param headless: 无头模式，默认为False（即显式打开浏览器）
    :return: Playwright Page 对象
    """
    # 1. 关闭所有正在运行的浏览器实例
    # close_all_browser_instances(browser_type)
    # time.sleep(2)


    # 2. 准备启动命令
    port = port or 9222
    # 使用临时目录作为用户数据目录，避免与现有浏览器配置冲突
    _user_data_dir = user_data_dir
    if user_data_dir_suffix:
        _user_data_dir = os.path.join(ALL_DATA_PATH, f".browser_data_{user_data_dir_suffix}")
        if not os.path.exists(_user_data_dir):
            os.makedirs(_user_data_dir)

    # browser_bin_path = get_default_browser_bin_path(browser_type)
    # if "不支持" in browser_bin_path:
    #     print(browser_bin_path)
    #     return None

    command = [
        browser_bin_path,
        f'--remote-debugging-port={port}',
        f'--user-data-dir={_user_data_dir}'
    ]
    if headless:
        command.append('--headless')

    # 3. 启动 browser
    print(f"正在启动 browser: {' '.join(command)}")
    try:
        subprocess.Popen(command)
    except Exception as e:
        raise ValueError(f"启动 browser 失败，请检查路径设置")
    time.sleep(3)  # 等待浏览器启动

    # 4. 连接到 Chrome
    try:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{port}")
        context = browser.contexts[0]
        page = context.new_page()
        print("成功连接到 Chrome 实例。")
    except Exception as e:
        print(f"连接到 Chrome 失败: {e}")
        print("请确保 Chrome 已成功启动，并且指定的路径正确。")
        return None

    return context, page


def close_all_browser_instances(browser_name='chrome'):
    """根据浏览器名称关闭所有实例"""
    system = platform.system()
    process_map = {
        'chrome': {'win': 'chrome.exe', 'mac': 'Google Chrome'},
        'edge': {'win': 'msedge.exe', 'mac': 'Microsoft Edge'}
    }
    
    if browser_name.lower() not in process_map:
        print(f"不支持的浏览器: {browser_name}")
        return

    proc_info = process_map[browser_name.lower()]
    proc_name = proc_info['win'] if system == 'Windows' else proc_info['mac']

    try:
        if system == 'Windows':
            subprocess.run(['taskkill', '/F', '/IM', proc_name], check=True, capture_output=True, text=True)
        elif system == 'Darwin':  # macOS
            subprocess.run(['killall', '-9', proc_name], check=True, capture_output=True, text=True)
        print(f"所有 {browser_name} 实例已关闭。")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"关闭 {browser_name} 时出错 (可能是因为没有正在运行的实例或命令未找到): {e}")




def click_item(page, css_locator, index=0):
    item = page.locator(css_locator)
    if item.count():
        item.nth(index).click()

def input_item(page, css_locator, index=0):
    item = page.locator(css_locator)
    if item.count():
        item.nth(index).click()

def get_default_browser_bin_path(browser_type):
    if browser_type.lower() == "chrome":
        if platform.system() == "Darwin":
            return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        elif platform.system() == "Windows":
            return "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    elif browser_type.lower() == "edge":
        if platform.system() == "Darwin":
            return "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
        elif platform.system() == "Windows":
            return "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
    return "不支持的类型或系统"