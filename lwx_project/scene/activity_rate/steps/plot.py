import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

import numpy as np
import pandas as pd

from lwx_project.scene.activity_rate.const import *
from lwx_project.utils.time_obj import TimeObj


def main():
    df = pd.read_excel(ACTIVITY_PATH)
    today = TimeObj()
    title = f"{{}}分行{today.month}月网点活动折线图"
    df.apply(lambda x: plot(df.columns[1:], x.values[1:], title.format(x.values[0])), axis=1)


def plot(x, y, title):
    plt.figure()
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
    plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

    fig, ax = plt.subplots(figsize=(14, 8))

    # 画折线图
    ax.plot([str(i) for i in x], y, "o-")

    # 设置x和y轴的标签
    ax.set_title(title)
    ax.set_xlabel('日期')
    ax.set_ylabel('活动率（%）')

    # 在10%和20%的地方画一条红线
    ax.axhline(y=0.1, color='r', linestyle='-')
    ax.axhline(y=0.2, color='r', linestyle='-')

    # 从0开始每隔2%画y_tick的灰色辅助线
    y_ticks = np.arange(0, max(max(y) * 1.2, 0.2), 0.02)
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(['{:.0f}%'.format(i * 100) for i in y_ticks])

    ax.grid(axis='y', linestyle='--', color='gray')
    plt.savefig(os.path.join(DATA_TMP_PATH, title + ".png"))


if __name__ == '__main__':
    main()