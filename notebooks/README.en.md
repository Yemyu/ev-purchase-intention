# Notebook guide

[中文](README.md) · [English](README.en.md) · [项目中文 README](../README.md) · [Project English README](../README.en.md)

## Choose a notebook

| File | Purpose |
|---|---|
| [`01_ev_purchase_intention_zh.ipynb`](01_ev_purchase_intention_zh.ipynb) | Chinese research notes, tables, and interpretation limits |
| [`01_ev_purchase_intention_en.ipynb`](01_ev_purchase_intention_en.ipynb) | English research notes, tables, and interpretation limits |

The two versions use the same code logic and translate the explanatory text, headings, and interpretation. Both call the shared `src.data_schema` mapping and read completed artifacts from one `figures/runs/run-*/` directory.

## Recommended workflow

1. Install `requirements.txt` in the project `.venv`.
2. Run the low-cost audit first:

   ```bash
   .venv/bin/python main.py --analysis audit
   ```

3. Run the full pipeline only when fresh results are needed:

   ```bash
   .venv/bin/python main.py --analysis all
   ```

4. Open the notebook in Jupyter.
5. The first code cell selects one complete local run and prints the project root, data path, and run ID. For a fixed release report, replace `RUN_ID = None` with an accepted run directory name.

The notebooks do not refit ordered logit, rerun bootstrap, rerun heterogeneity tests, or retrain the forest in the presentation layer. This keeps the CLI and notebooks on one question mapping and one set of results.

## What is displayed

The report covers:

- fixed question mapping and `primary`/`sensitivity`/`legacy` specifications;
- sample size, duplicates, missingness, composite diagnostics, data SHA256, and Git state;
- ordered-logit T/V odds ratios, intervals, p-values, and convergence;
- five exploratory bootstrap paths and intervals;
- LR statistics, raw p-values, and Holm-adjusted p-values for five groupings;
- held-out metrics for majority, ordered logit, and random forest across three feature sets;
- out-of-fold SHAP importance and SHAP run status;
- artifact existence, data-hash consistency, and failed-fold checks.

## Troubleshooting

**No `figures/runs/run-*` directory is found.**

Run `main.py --analysis audit` or `main.py --analysis all` from the repository root, then reopen the notebook. Run directories are ignored by Git so local survey artifacts are not committed automatically.

**Why not train models directly in the notebook?**

Training is centralized in `main.py` and `src/`. The notebook is a readable results report; this prevents the old notebook from silently redefining Q22, using a single train/test split, or changing forest settings.

**How does the report page differ from a dashboard?**

This is a one-time survey study rather than a continuously refreshed operational product. The repository now provides a read-only [GitHub Pages report](https://yemyu.github.io/ev-purchase-intention/) with aggregate audit, model, and prediction metrics. It does not load row-level responses or require continuous refresh, so an operational dashboard is still outside the current acceptance scope.

Both committed notebooks include executed tables and images, pinned to `run-20260921-190434`, and can be previewed on GitHub. Re-execution requires local run artifacts; the web aggregate JSON is committed.
