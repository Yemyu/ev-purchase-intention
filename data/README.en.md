# Data Documentation

[中文](README.md) · [English](README.en.md) · [Project README](../README.en.md)

## 1. Dataset overview

| Property | Description |
|---|---|
| Sample size | 622 respondents |
| Format | CSV exported from an online questionnaire |
| Target population | Chinese consumers considering an EV purchase |
| Main outcome | Q21: willingness to pay a premium for intelligent-driving functions |
| Response scale | Mostly ordinal 1–5 responses |
| Raw columns | 67, including questionnaire items and historical processing columns |

The current private repository contains `data/raw/data.csv` for local reproduction. It contains raw survey responses and must be removed, de-identified, or replaced with synthetic data before public release or external sharing.

## 2. Files and loading rules

| Path | Purpose |
|---|---|
| `data/raw/data.csv` | Local raw survey CSV used by the current pipeline |
| `src/config.py` | Fixed question numbers, headers, controls, and model specifications |
| `src/data_schema.py` | Question resolution, composites, control encoding, and audit |
| `figures/runs/<run-id>/audit.json` | Data-quality audit for one run |
| `figures/runs/<run-id>/run_metadata.json` | Data SHA256, seed, Git state, and mapping manifest |

The CSV may contain historical dummy and exception-handling columns. The new pipeline resolves Q1–Q29 by explicit question number and unsuffixed raw headers. It does not select columns by position and does not pass historical processing columns into a model.

## 3. Variable definitions

### 3.1 Outcome, core proxies, and exploratory mediators

| Symbol | Meaning | Raw items | Construction | Role |
|---|---|---|---|---|
| `Y` | Willingness to pay a premium for intelligent-driving functions | Q21 | Single ordinal item, 1–5 | Outcome |
| `T` | Technology importance and safety recognition | Q15, Q16 | Row mean when all items are present | Core predictor |
| `V` | Value recognition for concrete assisted-driving functions | Q22–Q25 | Row mean when all items are present | Core predictor |
| `M1` | Recognition of improved driving pleasure | Q18 | Single item, 1–5 | Exploratory mediator |
| `M2` | Recognition of improved travel efficiency | Q19 | Single item, 1–5 | Exploratory mediator |

T and V are **project-defined proxies**, not externally validated scales. `data_schema.py` reports complete rows, means, standard deviations, and Cronbach's alpha for item composites. Those diagnostics document the data and do not trigger post-hoc item selection.

### 3.2 Three fixed model specifications

| Specification | T | V | Control encoding | Purpose |
|---|---|---|---|---|
| `primary` | `mean(Q15, Q16)` | `mean(Q22, Q23, Q24, Q25)` | Categorical dummies | Current main analysis |
| `sensitivity` | `mean(Q15, Q16, Q17)` | `mean(Q22, Q23, Q24, Q25)` | Categorical dummies | Checks inclusion of Q17 |
| `legacy` | `mean(Q15, Q16)` | `Q22` | Original ordinal codes | Traces the earlier project |

The primary specification is fixed before fitting. It is not chosen from p-values, VIF, or machine-learning scores. `legacy` is retained for traceability and is not the current recommended measurement.

### 3.3 Fixed controls

| Name | Question | Source codes | Main/sensitivity treatment |
|---|---:|---|---|
| `gender` | Q1 | 1–2 | Categorical dummies, first level reference |
| `age` | Q2 | 1–5 | Categorical dummies, first level reference |
| `education` | Q4 | 1–4 | Categorical dummies, first level reference |
| `income` | Q6 | 1–5 | Categorical dummies, first level reference |
| `driving_exp` | Q9 | 1–5 | Categorical dummies, first level reference |
| `driving_freq` | Q12 | 1–5 | Categorical dummies, first level reference |

Codes refer to questionnaire categories. The code does not infer age in years, income amounts, or driving-license years. Missing controls are not silently converted into the reference category; model modules apply their declared complete-case rule.

## 4. Raw question mapping

| No. | Original Chinese question |
|---:|---|
| Q1 | 您的性别是? |
| Q2 | 您的年龄是? |
| Q3 | 您所在的区域是? |
| Q4 | 您的最高学历是? |
| Q5 | 您的职业是? |
| Q6 | 您的月收入范围是? |
| Q7 | 您的家庭常住人口数是? |
| Q8 | 您未来购买汽车的意向是? |
| Q9 | 您的驾龄是? |
| Q10 | 您驾驶的主要目的是? |
| Q11 | 您每天的日常通勤距离大约是? |
| Q12 | 您每周驾驶的频率是? |
| Q13 | 您通常的驾驶时间段是? |
| Q14 | 您通常驾驶的车辆类型是? |
| Q15 | 您认为智能驾驶功能对新能源汽车很重要? |
| Q16 | 您认为智能驾驶功能可以提高驾驶安全性? |
| Q17 | 您认为智能驾驶功能可以减轻驾驶疲劳? |
| Q18 | 您认为智能驾驶功能可以提升驾驶乐趣? |
| Q19 | 您认为智能驾驶功能可以提高出行效率? |
| Q20 | 智能驾驶功能会影响您购买新能源汽车的决策? |
| Q21 | 您愿意为智能驾驶功能支付溢价? |
| Q22 | 您愿意为智能驾驶的自适应巡航功能影响购买意愿? |
| Q23 | 您愿意为智能驾驶的车道保持辅助功能影响购买意愿? |
| Q24 | 您愿意为智能驾驶的自动泊车功能影响购买意愿? |
| Q25 | 您愿意为智能驾驶的交通拥堵辅助功能影响购买意愿? |
| Q26 | 您愿意为智能驾驶未来技术更加成熟影响购买意愿? |
| Q27 | 您愿意为智能驾驶未来安全性更高影响购买意愿? |
| Q28 | 您愿意为智能驾驶未来成本更低影响购买意愿? |
| Q29 | 您愿意为智能驾驶未来应用场景更丰富影响购买意愿? |

Q8, Q20, and Q26–Q29 are excluded from the current main feature set because they change the research question, overlap conceptually with the outcome, or describe future scenarios. They remain in the raw file and are not deleted by the audit.

## 5. Quality and missing-data policy

- Raw items are converted to numeric; values that cannot be converted become missing and are reported.
- Composite means use complete item rows. If one item in a composite is missing, the composite remains missing for that respondent.
- The default valid response range is 1–5; out-of-range values are reported, not silently clipped.
- Each model module applies its declared complete-case rule and records `n_obs`.
- The audit records duplicates, item missingness, out-of-range values, control categories, and historical processing columns.
- No question is changed after inspecting p-values or model performance.

## 6. Analysis artifacts

A complete run creates `figures/runs/run-YYYYMMDD-HHMMSS/` with:

- `audit.json`: data and variable audit;
- `run_metadata.json`: data SHA256, seed, Python version, Git state, and mapping manifest;
- `ordered_logit_coefficients.csv`: coefficients and odds ratios for all three specifications;
- `mediation_paths.csv`: five exploratory paths and bootstrap intervals;
- `heterogeneity_results.csv`: LR statistics, raw p-values, and Holm-adjusted p-values;
- `ml_summary.csv`, `ml_oof_predictions.csv`: held-out metrics and predictions;
- `shap_importance.csv`, `shap_importance.png`: out-of-fold forest attribution.

The notebooks read saved artifacts rather than redefining questions or retuning models. Interpret results as cross-sectional conditional associations, exploratory indirect associations, and out-of-fold predictive explanations.

## 7. Privacy and public release

The repository is currently private and includes the raw CSV for local reproduction. Before making it public or sending it to reviewers:

1. check for direct and combination-identification risks;
2. remove the raw survey or use an approved de-identified/synthetic sample;
3. retain the data dictionary, mapping manifest, and run metadata so the construction is auditable; and
4. document why the raw data cannot be published and how compliant access could be requested.

This repository does not modify the thesis. If the thesis still uses the legacy single-item V definition, document that version boundary so readers do not treat the two sets of numbers as one specification.
