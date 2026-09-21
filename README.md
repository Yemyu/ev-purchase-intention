# EV Purchase Intention

<div align="center">

**新能源汽车智能驾驶功能与购买溢价意愿：问卷经济分析与机器学习补充验证**

[中文](README.md) · [English](README.en.md) · [数据字典 / Data documentation](data/README.md) · [Notebook 导航 / Notebook guide](notebooks/README.md) · [研究报告页 / Report page](https://yemyu.github.io/ev-purchase-intention/)

</div>

> 本仓库是一个研究型分析项目。它把有序响应模型作为主分析，再用折外机器学习和 SHAP 做预测层面的补充解释。项目不把预测解释写成因果结论，也不修改论文原文。

## 项目在回答什么问题

本项目使用 622 份问卷，研究受访者对智能驾驶功能的认知是否与新能源汽车购买溢价意愿相关，并进一步检查：

1. 技术重要性与安全性认知（T）是否与购买溢价意愿（Y）正相关；
2. 对具体辅助驾驶功能的功能价值认知（V）是否与 Y 正相关；
3. 驾驶乐趣（M1）和出行效率（M2）是否提供探索性的间接路径；
4. 这些关联是否随人口统计分组而变化；
5. 机器学习能否在折外样本中复现购买意愿的排序信息，以及哪些变量对预测最有贡献。

研究结论的适用范围是**横截面问卷中的条件关联和预测表现**。项目不声称识别因果效应，也不把 SHAP 重要性当作因果贡献。

## 研究设计一览

```text
原始问卷 CSV
    │
    ├─ 显式题号映射、缺失/范围/重复审计
    │
    ├─ 有序 Logit：Y ~ T + V + 固定控制变量       ← 主结果
    │
    ├─ Bootstrap 间接路径：T/V → M1/M2 → Y       ← 探索性
    │
    ├─ 嵌套模型 LR + Holm 校正                   ← 异质性
    │
    └─ 5 折折外预测 + SHAP                       ← 计算补充
```

主分析不从 p 值或模型得分反向挑选题目。所有题号、变量定义、控制变量和缺失规则都集中写在 [`src/config.py`](src/config.py) 与 [`src/data_schema.py`](src/data_schema.py) 中。

## 数据与变量

仓库当前为公开仓库，原始 CSV 仍随项目版本保存，用于复现 622 行、67 列的分析。网页只加载聚合后的报告 JSON；分析流程只读取明确的原始题号列，不会把历史哑变量或异常处理列误传入模型。

| 符号 | 含义 | 当前主规格 |
|---|---|---|
| `Y` | 愿意为智能驾驶功能支付溢价 | Q21，1–5 有序变量 |
| `T` | 技术重要性与安全性认知代理变量 | `mean(Q15, Q16)` |
| `V` | 具体辅助驾驶功能的功能价值代理变量 | `mean(Q22, Q23, Q24, Q25)` |
| `M1` | 驾驶乐趣认知 | Q18 |
| `M2` | 出行效率认知 | Q19 |

项目保留三套固定规格，便于追踪旧版本和检查测量口径的影响：

| 规格 | T | V | 控制变量处理 | 用途 |
|---|---|---|---|---|
| `primary` | Q15、Q16 均值 | Q22–Q25 均值 | 分类哑变量 | 当前主规格 |
| `sensitivity` | Q15–Q17 均值 | Q22–Q25 均值 | 分类哑变量 | 加入“减轻驾驶疲劳”后的敏感性检查 |
| `legacy` | Q15、Q16 均值 | Q22 单题 | 原始有序编码 | 追踪旧项目口径，不作为当前首选 |

T 和 V 是项目内定义的**代理变量**，不是经过外部量表验证的完整心理构念。审计会记录题项缺失、取值范围、题项相关和 Cronbach's alpha，但不会因为 alpha 或显著性而事后删题。

完整变量说明、原始题目和隐私处理见 [`data/README.md`](data/README.md)。

## 分析模块与结果解释

### 1. 数据审计

`main.py --analysis audit` 会记录样本量、重复行、题号解析、1–5 范围检查、每题缺失、控制变量类别、历史处理列数量和组合题项诊断。审计是数据质量记录，不会静默修正原始 CSV。

### 2. 有序 Logit 直接关联

主模型把 Q21 作为有序结果，加入 T、V 和六项固定背景控制变量。输出包括系数、优势比（OR）、置信区间、p 值、样本量、收敛状态和辅助 VIF。结果应写成“在控制其他变量后，较高的 T/V 与较高的 Y 发生概率相关”，不能写成“提高了购买意愿”或“产生了因果影响”。

### 3. Bootstrap 间接路径

固定五条路径：

- `T → M1 → Y`
- `T → M2 → Y`
- `V → M1 → Y`
- `V → M2 → Y`
- `T → V → Y`

每条路径使用 5,000 次 bootstrap，并记录有效次数、失败次数和区间。由于中间方程采用探索性的 respondent-level OLS 近似，这部分只作为间接关联证据，不标注因果中介、完全/部分中介或因果效应占比。

### 4. 异质性

对性别、年龄、收入、驾龄和驾驶频率分别比较受限模型与加入 `T/V × 分组` 交互项的嵌套有序 Logit。自由度按实际设计矩阵秩差计算，同时报告原始 p 值和 Holm 校正后的 p 值。多重比较校正后未形成稳定的 0.05 水平群体差异，因此该模块应写成探索性结果。

### 5. 机器学习与 SHAP

使用相同的 5 个分层折比较：

- 多数类基线；
- 有序 Logit；
- 随机森林；
- `controls`、`core`（控制变量 + T/V）和 `extended`（再加入 M1/M2）三组特征。

报告准确率、macro-F1、二次加权 Kappa（QWK）、有序 MAE、每折结果、折外预测和混淆矩阵。SHAP 在折外随机森林上计算；若当前 SHAP 版本不支持高购买意愿概率输出，会在 `ml_run_metadata.json` 中记录 raw-output fallback。SHAP 仅说明预测模型的特征归因，不是独立的因果验证。

## 快速开始

请始终在项目虚拟环境中安装和运行依赖：

```bash
python3 -m venv .venv
uv pip install --offline --python .venv/bin/python -r requirements.txt
```

如果本地没有离线缓存，也请在 `.venv` 内通过常用镜像安装，不要污染系统 Python。

先做低成本审计：

```bash
.venv/bin/python main.py --analysis audit
```

按模块运行：

```bash
.venv/bin/python main.py --analysis econometrics
.venv/bin/python main.py --analysis mediation
.venv/bin/python main.py --analysis heterogeneity
.venv/bin/python main.py --analysis ml
```

运行完整流程：

```bash
.venv/bin/python main.py --analysis all
```

完整流程默认使用 5,000 次 bootstrap。调试时可以显式降低次数，例如：

```bash
.venv/bin/python main.py --analysis mediation --bootstrap-iterations 50
```

每次运行都会在 `figures/runs/run-YYYYMMDD-HHMMSS/` 创建独立目录，保存数据 SHA256、题号映射、随机种子、Python 环境、Git 状态和模块输出。运行目录默认被 `.gitignore` 忽略；如果要给审阅者展示结果，应另行提交脱敏的汇总文件。

## Notebook

Notebook 现在按语言和分析职责分开：

- [`01_ev_purchase_intention_zh.ipynb`](notebooks/01_ev_purchase_intention_zh.ipynb)：中文研究说明与结果解读；
- [`01_ev_purchase_intention_en.ipynb`](notebooks/01_ev_purchase_intention_en.ipynb)：英文研究说明与结果解读；
- [`notebooks/README.md`](notebooks/README.md)：运行顺序、结果目录选择和常见问题。

两个 Notebook 都调用 `src.data_schema` 的统一题号映射，并读取 `figures/runs/` 的结果文件，不再复制旧版 Q22 单题定义、单次 train/test split 或旧版随机森林流程。Notebook 默认不自动启动高成本完整运行；需要重新计算时先执行命令行入口，再打开 Notebook 查看结果。

## 为什么保留报告页而不做运营看板

本项目的交付物是可复现的研究分析，不是面向运营人员的持续监控产品。样本是一次性问卷，主要输出是模型表、置信区间和方法说明，因此当前版本提供一个只读静态报告页，集中展示审计、OR、Bootstrap 区间和 ML 指标；不额外制作需要持续刷新数据的运营看板。

报告页地址：<https://yemyu.github.io/ev-purchase-intention/>。它由 `app/` 目录和 GitHub Pages 工作流发布，Notebook 与完整分析代码仍保留在仓库中。

## 项目结构

```text
src/config.py             固定题号、变量规格、控制变量和运行参数
src/data_schema.py        原始数据读取、审计、组合变量和控制变量编码
src/ordered_logit.py      有序 Logit 直接关联与 VIF
src/mediation.py          五条探索性 Bootstrap 间接路径
src/heterogeneity.py      嵌套交互模型与 LR/Holm 检验
src/ml_shap.py            折外预测、指标和 SHAP
main.py                   命令行入口与运行元数据
notebooks/                中英文 Notebook 与导航
data/README.md            中英文数据字典和隐私说明
figures/                  历史图表及本地运行结果
IMPLEMENTATION_PLAN.md    已锁定的设计、边界与验收规则
```

## 研究边界与数据隐私

- 数据来自一次性在线问卷，存在横截面、便利样本、自报和共同方法偏差。
- T/V 是代理变量，不能替代经过验证的成熟量表。
- 结果适合项目展示和方法演示，不应被表述为普遍人口的因果估计。
- 当前仓库为公开仓库，原始问卷 CSV 按项目所有者的发布决定保留，用于本项目复现；网页不加载逐行数据。未经项目所有者授权，不应将问卷原始回答用于其他用途或再次分发。
- 本项目不修改论文文档；如果论文仍使用旧的 Q22 单题 V 定义，应在论文与代码之间明确区分版本。

## License and citation

代码按仓库中的 [`LICENSE`](LICENSE) 发布。若使用问卷数据或分析框架，请同时说明数据采集、变量构造、样本限制和本仓库的版本信息。

GitHub 仓库：<https://github.com/Yemyu/ev-purchase-intention>
