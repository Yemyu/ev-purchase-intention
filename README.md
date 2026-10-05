<p align="center">
  <a href="README.md">中文</a> · <a href="README.en.md">English</a>
</p>

<h1 align="center">智能驾驶功能与新能源汽车支付溢价意愿</h1>

<p align="center">基于 622 份消费者问卷的计量分析与机器学习研究</p>

<p align="center">
  <a href="notebooks/01_ev_purchase_intention_zh.ipynb">分析 Notebook</a> ·
  <a href="https://yemyu.github.io/ev-purchase-intention/">报告页</a>
</p>

---

本项目研究消费者对智能驾驶技术和具体辅助驾驶功能的评价，与支付溢价意愿之间的关系。分析包括有序 Logit、探索性间接路径、人群差异检验，以及有序 Logit 与随机森林的预测比较。

## 主要结果

| 分析 | 结果 |
|---|---|
| 有序 Logit | 加入六项背景控制变量后，技术认知 T 的 OR 为 **2.08**（95% CI：1.62–2.68），功能价值 V 的 OR 为 **3.83**（2.84–5.16）；两项 p < 0.001 |
| 间接路径 | 五条路径的 Bootstrap 95% 区间均高于 0，间接关联估计为 0.163–0.351 |
| 人群差异 | 性别、年龄、收入、驾龄和驾驶频率的五项交互检验，经 Holm 校正后均未达到 0.05 显著性水平 |
| 预测比较 | 加入 T、V、驾驶乐趣和出行效率后，有序 Logit 的五折平均 QWK 为 **0.685**、准确率为 **54.5%**；随机森林分别为 **0.619**、**53.5%** |
| SHAP | 扩展随机森林预测高溢价意愿的概率时，功能价值、技术认知、驾驶乐趣和出行效率的平均绝对 SHAP 值排在前四 |

完整表格、图和分析说明见报告页与已执行的 Notebook。

## 数据与变量

数据为 622 份在线问卷，CSV 共 67 列，其中 29 列为原始题项。分析按题号和原始列名读取所需回答。

| 符号 | 含义 | 构造 |
|---|---|---|
| Y | 为智能驾驶功能支付溢价的意愿 | Q21，1–5 有序等级 |
| T | 技术认知：重要性与安全性评价 | Q15、Q16 的均值 |
| V | 功能价值：四项辅助驾驶功能的评价 | Q22–Q25 的均值 |
| M1 | 驾驶乐趣评价 | Q18，单题 |
| M2 | 出行效率评价 | Q19，单题 |

控制变量为性别、年龄、学历、收入、驾龄和驾驶频率，按问卷类别编码。组合指标要求所用题项回答完整，各模型使用其所需变量的完整记录。

原始题目、类别代码和缺失值规则见[数据说明](data/README.md)。

## 四个分析模块

### 有序 Logit

以 Y 的五个有序等级为结果，同时纳入 T、V 和六项控制变量。报告系数、优势比、95% 置信区间及 p 值。优势比对应 T 或 V 增加 1 分后的调整关联；主模型样本为 622 人。

### 探索性间接路径

分别估计 T→M1→Y、T→M2→Y、V→M1→Y、V→M2→Y 和 T→V→Y。每条路径使用含控制变量的 OLS 方程，并按受访者有放回抽样 5,000 次，计算系数乘积的百分位区间。

### 人群差异

对五个人口特征与驾驶经历分组，比较加入 T、V 交互项前后的嵌套有序 Logit 模型。采用似然比检验，并用 Holm 方法校正五项比较。

### 预测比较与 SHAP

多数类基线、有序 Logit 和随机森林使用同一组五折分层交叉验证，随机种子为 42。比较仅背景变量、加入 T/V、再加入 M1/M2 三组输入，报告准确率、宏平均 F1、二次加权 Kappa（QWK）和等级 MAE。随机森林使用 200 棵树、最大深度 6。SHAP 在各折测试样本上解释扩展随机森林的 P(Y≥4)，汇总全部 23 个输入特征。

模型方程、指标定义及研究局限见[分析方法](docs/METHODS.md)。

## 快速开始

已保存的 Notebook 输出和报告页可直接阅读。重新计算使用 Python 3.12。

### 1. 克隆项目

```bash
git clone https://github.com/Yemyu/ev-purchase-intention.git
cd ev-purchase-intention
```

### 2. 安装依赖

macOS / Linux：

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Windows（PowerShell）：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

激活环境后：

```bash
python -m pip install -r requirements.txt
```

### 3. 运行分析

```bash
python main.py --analysis audit
python main.py --analysis all
```

`audit` 生成数据质量记录；`all` 生成完整分析结果，包括 5,000 次 Bootstrap。结果保存在 `figures/runs/run-YYYYMMDD-HHMMSS/`。

各模块也可以分别运行：

```bash
python main.py --analysis econometrics
python main.py --analysis mediation
python main.py --analysis heterogeneity
python main.py --analysis ml
```

### 4. 查看 Notebook

```bash
jupyter lab
```

打开中文或英文 Notebook。重新执行时，Notebook 读取最近一个完整运行目录；指定目录的方法见 [Notebook 说明](notebooks/README.md)。

## 项目结构

```text
main.py              命令行分析入口
src/                 数据处理、计量模型、间接路径、分组检验与预测
notebooks/           中英文分析 Notebook
app/                 报告页与汇总数据
data/raw/data.csv    问卷数据
data/README.md       数据字典
docs/METHODS.md      分析方法与研究局限
figures/runs/        本地生成的分析结果
archive/             历史图表与报告布局
requirements.txt     Python 依赖
```

报告页的本地预览和结果更新见 [app/README.md](app/README.md)。

## 研究局限

问卷为横截面便利样本，结论描述样本中的关联和预测表现。Y 测量支付溢价意愿，不能代替实际购买行为。T、V 为题项组合指标，未经外部量表验证；V 题目本身涉及购买意愿，与 Y 存在概念接近性。

题项曾在同一数据上进行探索，当前交叉验证未覆盖此前的选题过程。有序 Logit 的比例优势假设尚未专项检验。间接路径采用评分连续化的 OLS 近似，SHAP 描述预测模型的特征归因。

## 数据使用与许可证

仓库包含原始问卷回答，报告页使用汇总数据。问卷数据的复用和再分发需取得相应授权。

代码采用 [MIT License](LICENSE)。
