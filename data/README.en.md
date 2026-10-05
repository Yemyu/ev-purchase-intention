# Data documentation

[中文](README.md) · [English](README.en.md) · [Project overview](../README.en.md)

## Dataset

| Property | Description |
|---|---|
| Sample | 622 consumer survey responses |
| Format | CSV exported from an online questionnaire |
| File | `data/raw/data.csv` |
| Columns | 67: 29 original items and 38 existing processing columns |
| Outcome | Q21: willingness to pay a premium for driver-assistance features |

The research report uses aggregate JSON. Analysis reads original items from the CSV. Headers and question mappings are in [`src/config.py`](../src/config.py); processing is in [`src/data_schema.py`](../src/data_schema.py).

## Research variables

| Symbol | Meaning | Items | Construction and coding |
|---|---|---|---|
| Y | Willingness to pay a premium | Q21 | Single ordered item, 1–5 |
| T | Technology perceptions: importance and safety | Q15, Q16 | Arithmetic mean when both items are answered |
| V | Perceived feature value | Q22–Q25 | Arithmetic mean when all four items are answered |
| M1 | Perceived driving pleasure | Q18 | Single item, 1–5 |
| M2 | Perceived travel efficiency | Q19 | Single item, 1–5 |

T and V are item composites. Their internal-consistency alpha values are 0.858 and 0.871. See [analysis methods](../docs/METHODS.en.md) for measurement interpretation and limitations.

### Controls

| Variable | Item | Configured category codes | Model encoding |
|---|---|---|---|
| Gender | Q1 | 1–2 | Category dummies, category 1 as reference |
| Age | Q2 | 1–5 | As above |
| Education | Q4 | 1–4 | As above |
| Monthly income | Q6 | 1–5 | As above |
| Driving experience | Q9 | 1–5 | As above |
| Weekly driving frequency | Q12 | 1–5 | As above |

Codes identify questionnaire options. Complete option labels are not available in the repository, so charts retain category codes rather than infer age bands, income amounts or years of experience. Four income categories occur in the current data.

Q3 is a region category item with recorded codes 1–8 and 110 missing responses. It is not used in the reported models. Other unused items remain in the source CSV.

## Original questionnaire items

The original Chinese headers are preserved below. English summaries describe the topics rather than replace the source wording. A CSV header combines the question number, a period and the original text.

| Item | Original Chinese wording | English topic summary |
|---|---|---|
| Q1 | 您的性别是? | Gender |
| Q2 | 您的年龄是? | Age |
| Q3 | 您所在的区域是? | Region |
| Q4 | 您的最高学历是? | Education |
| Q5 | 您的职业是? | Occupation |
| Q6 | 您的月收入范围是? | Monthly income |
| Q7 | 您的家庭常住人口数是? | Household size |
| Q8 | 您未来购买汽车的意向是? | Future vehicle-purchase plans |
| Q9 | 您的驾龄是? | Driving experience |
| Q10 | 您驾驶的主要目的是? | Main driving purpose |
| Q11 | 您每天的日常通勤距离大约是? | Daily commuting distance |
| Q12 | 您每周驾驶的频率是? | Weekly driving frequency |
| Q13 | 您通常的驾驶时间段是? | Usual driving time |
| Q14 | 您通常驾驶的车辆类型是? | Usual vehicle type |
| Q15 | 您认为智能驾驶功能对新能源汽车很重要? | Importance of driver-assistance features |
| Q16 | 您认为智能驾驶功能可以提高驾驶安全性? | Perceived safety benefit |
| Q17 | 您认为智能驾驶功能可以减轻驾驶疲劳? | Perceived fatigue reduction |
| Q18 | 您认为智能驾驶功能可以提升驾驶乐趣? | Perceived driving pleasure |
| Q19 | 您认为智能驾驶功能可以提高出行效率? | Perceived travel efficiency |
| Q20 | 智能驾驶功能会影响您购买新能源汽车的决策? | Driver assistance and EV purchase decisions |
| Q21 | 您愿意为智能驾驶功能支付溢价? | Willingness to pay a premium |
| Q22 | 您愿意为智能驾驶的自适应巡航功能影响购买意愿? | Adaptive cruise control and purchase intention |
| Q23 | 您愿意为智能驾驶的车道保持辅助功能影响购买意愿? | Lane-keeping assistance and purchase intention |
| Q24 | 您愿意为智能驾驶的自动泊车功能影响购买意愿? | Parking assistance and purchase intention |
| Q25 | 您愿意为智能驾驶的交通拥堵辅助功能影响购买意愿? | Traffic-jam assistance and purchase intention |
| Q26 | 您愿意为智能驾驶未来技术更加成熟影响购买意愿? | Future technical maturity and purchase intention |
| Q27 | 您愿意为智能驾驶未来安全性更高影响购买意愿? | Future safety and purchase intention |
| Q28 | 您愿意为智能驾驶未来成本更低影响购买意愿? | Future cost reduction and purchase intention |
| Q29 | 您愿意为智能驾驶未来应用场景更丰富影响购买意愿? | Future application coverage and purchase intention |

## Processing

- Items are resolved by original header and question number. Existing processing columns are excluded from model inputs.
- Responses are converted to numeric; values that cannot be converted are marked missing.
- T and V require complete item responses. A missing component produces a missing composite.
- Q15–Q29 use ratings from 1 to 5; background items are read using their own category ranges.
- Models use complete records for their required variables. The main items and controls have no missing responses in this dataset; the main model uses 622 records.
- `audit.json` records duplicates, missingness, ranges and composite statistics.

## Result files

A full run writes to `figures/runs/run-YYYYMMDD-HHMMSS/`.

| File | Content |
|---|---|
| `audit.json` | Sample and item diagnostics |
| `ordered_logit_coefficients.csv` | Coefficients, odds ratios, intervals and p-values |
| `ordered_logit_diagnostics.json` | Fitting diagnostics |
| `mediation_paths.csv` | Five indirect paths and bootstrap intervals |
| `heterogeneity_results.csv` | Group LR tests and Holm adjustment |
| `ml_summary.csv` | Five-fold mean metrics by model and input set |
| `ml_fold_metrics.csv` | Fold metrics |
| `ml_oof_predictions.csv` | Held-out predictions |
| `shap_importance.csv` | Mean absolute SHAP ranking |
| `run_metadata.json` | Data and code versions and run configuration |

Notebooks read these files to present research tables and figures. See the [notebook guide](../notebooks/README.en.md) for execution and directory selection.

## Data use

The raw CSV contains respondent answers. Reuse or redistribution requires the relevant authorization. The report page loads aggregate data only. Code is released under the [MIT License](../LICENSE).
