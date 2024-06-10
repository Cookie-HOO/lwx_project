# 李文萱的工作空间项目

## 设计思路
1. GUI
    - 打开后，需要登录，登录成功后进入主页面
    - 主页面左右分布，左边是场景，右边是场景详情

2. 项目结构
    conf
        场景1.json
    data
        场景1
            important
            tmp
            result
    lwx_project
        client：客户端相关代码
        scene：场景相关代码
        utils：工具函数
    static
        静态资源目录

## 一些问题
1. pyinstaller的打包问题
    - 先用pyinstaller打包一下
        pyinstaller -Fw .\lwx_project\main.py
    - 找到根目录的main.spec文件
        pathex=["..\lwx_project"],  # 将当前项目根目录添加进去
    - 再次打包
        pyinstaller .\main.spec --distpath=.

2. GUI的选型问题
    tkinter：无法设置透明文字
        tk.Label的背景无法透明，在有背景图片时存在问题
    pyqt5:
        高版本的python3.12，安装pytqt5-tools时，报错poetry的兼容问题
        降级到python3.7后，安装pyqt5时，报错找不到C++ Microsoft 组件，需要下载
            配置pyqt5+designer with pycharm：
                https://blog.csdn.net/m0_57021623/article/details/123459038
            报错找不到C++ Microsoft 组件的方法
                https://blog.csdn.net/qq_37553692/article/details/128996821
    最终从后续的扩展性考虑，选择pyqt