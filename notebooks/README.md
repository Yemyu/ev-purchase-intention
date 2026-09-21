# Notebook 导航 / Notebook guide

[中文](README.md) · [English](README.en.md) · [项目中文 README](../README.md) · [Project English README](../README.en.md)

## 选择哪个 Notebook

| 文件 | 用途 |
|---|---|
| [`01_ev_purchase_intention_zh.ipynb`](01_ev_purchase_intention_zh.ipynb) | 中文研究说明、表格和解释边界 |
| [`01_ev_purchase_intention_en.ipynb`](01_ev_purchase_intention_en.ipynb) | English research notes, tables, and interpretation limits |

两个版本的代码逻辑相同，只翻译说明、标题和解释文字。它们都使用 `src.data_schema` 的统一题号映射，并从同一个 `figures/runs/run-*/` 目录读取已经完成的结果。

## 推荐运行顺序

1. 在项目根目录的 `.venv` 中安装 `requirements.txt`。
2. 先执行一次低成本审计：

   ```bash
   .venv/bin/python main.py --analysis audit
   ```

3. 需要更新完整结果时再执行：

   ```bash
   .venv/bin/python main.py --analysis all
   ```

4. 在 Jupyter 中打开对应语言的 Notebook。
5. 第一段代码会选择一个完整的本地运行目录，并打印路径、数据文件和运行 ID。发布固定报告时，可以把 `RUN_ID = None` 改成已经验收的具体目录名。

Notebook 不在展示层重新运行有序 Logit、Bootstrap、异质性或随机森林。这样可以避免 Notebook 与命令行入口分别产生两套题号映射和两套结果。

## 输出内容

Notebook 依次展示：

- 固定题号映射和 `primary`/`sensitivity`/`legacy` 规格；
- 样本量、重复行、缺失、组合题项诊断、数据 SHA256 和 Git 状态；
- 有序 Logit 的 T/V OR、置信区间、p 值和收敛状态；
- 五条探索性 Bootstrap 间接路径及其区间；
- 五个分组的 LR、原始 p 值和 Holm 校正 p 值；
- 多数类、Ordered Logit、随机森林在三组特征集上的折外指标；
- 折外 SHAP 重要性和 SHAP 运行状态；
- 结果文件存在性、数据哈希一致性和失败折检查。

## 常见问题

**没有找到 `figures/runs/run-*`。**

请先从项目根目录执行 `main.py --analysis audit` 或 `main.py --analysis all`，再重新打开 Notebook。运行目录默认被 Git 忽略，不代表代码没有结果，而是为了避免把本地问卷分析产物自动提交到仓库。

**为什么不在 Notebook 里直接训练模型？**

模型训练统一由 `main.py` 和 `src/` 完成。Notebook 只是一个可读的结果报告，避免旧版 Notebook 重新定义 Q22、单次切分和随机森林参数。

**为什么没有看板？**

这是一次性问卷研究，不是持续更新的运营数据产品。静态图表、CSV 和 JSON 更容易审计，也足够支撑当前展示；看板可以作为未来的可选展示层，不是当前验收条件。
