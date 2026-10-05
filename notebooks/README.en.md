# Notebooks

[中文](README.md) · [English](README.en.md) · [Project overview](../README.en.md) · [Research report](https://yemyu.github.io/ev-purchase-intention/en.html)

## View results

| File | Contents |
|---|---|
| [Chinese notebook](01_ev_purchase_intention_zh.ipynb) | Chinese commentary, result tables and figures |
| [English notebook](01_ev_purchase_intention_en.ipynb) | English commentary, result tables and figures |

Both notebooks contain executed outputs and can be read directly on GitHub without installing dependencies. They present the same analysis and numerical results, with translated commentary, table headers, legends and chart labels.

The sections cover data and variables, ordered logit, five exploratory indirect paths, demographic interaction tests, five-fold predictive comparison with SHAP, and limitations.

## Re-execute locally

Work from the repository root. Follow the environment setup and activation instructions in [Quick start](../README.en.md#quick-start), then run:

```bash
python main.py --analysis all
jupyter notebook notebooks/01_ev_purchase_intention_en.ipynb
```

To open the Chinese version:

```bash
jupyter notebook notebooks/01_ev_purchase_intention_zh.ipynb
```

`main.py --analysis all` generates complete analysis results, including 5,000 bootstrap draws and five-fold predictions. The notebooks read these files and produce the presentation without refitting models. The `--analysis audit` option produces sample checks only and does not generate all model results required by the notebooks.

## Result directory

The default `RUN_ID = None` selects the latest directory by name under `figures/runs/run-*` that contains all required files. A specific directory name can be used to select a fixed run. Every table and figure uses files from the same directory.

Run directories are not committed to Git. Saved notebook outputs remain readable after cloning, but re-executing the cells requires a complete local run. The notebooks check required files, data consistency and analysis status, and stop if files are incomplete or inconsistent.

Rendering the Chinese figures requires a Chinese-capable font, such as PingFang SC, Microsoft YaHei or Noto Sans CJK SC.
