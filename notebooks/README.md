# Notebook

[中文](README.md) · [English](README.en.md) · [项目说明](../README.md) · [报告页](https://yemyu.github.io/ev-purchase-intention/)

## 查看结果

| 文件 | 内容 |
|---|---|
| [中文 Notebook](01_ev_purchase_intention_zh.ipynb) | 中文说明、结果表和图表 |
| [English Notebook](01_ev_purchase_intention_en.ipynb) | 英文说明、结果表和图表 |

两份 Notebook 均已执行并保存输出，可直接在 GitHub 查看，无需安装依赖。它们展示同一次分析，数值一致；说明、表头、图例和图中标签分别使用中文与英文。

内容包括数据与变量、有序 Logit、五条探索性间接路径、人群差异检验、五折预测比较与 SHAP，以及研究局限。

## 在本地重新执行

从项目根目录操作。环境安装和激活方法见 [快速开始](../README.md#快速开始)。激活环境后，运行：

```bash
python main.py --analysis all
jupyter notebook notebooks/01_ev_purchase_intention_zh.ipynb
```

英文版的启动命令：

```bash
jupyter notebook notebooks/01_ev_purchase_intention_en.ipynb
```

`main.py --analysis all` 生成完整分析结果，包括 5,000 次 Bootstrap 和五折预测。Notebook 读取这些结果、生成展示，不重新估计模型。单独运行 `--analysis audit` 只生成样本检查，不能提供 Notebook 所需的全部模型结果。

## 结果目录

Notebook 默认使用 `RUN_ID = None`，选择 `figures/runs/` 下名称排序最新、且包含全部必需文件的 `run-*` 目录。设置具体目录名可固定读取某次分析；所有表格和图使用同一个目录。

运行目录不随 Git 提交。克隆仓库后，已保存的 Notebook 输出仍可直接阅读；重新执行代码需要先生成完整结果。Notebook 会检查结果目录、数据一致性及模型运行状态，发现不完整或不匹配的文件时停止执行。

中文图表需要支持中文的字体，如苹方、微软雅黑或 Noto Sans CJK SC。
