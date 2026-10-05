# Research report

[中文](README.md) · [English](README.en.md) · [Project overview](../README.en.md)

The bilingual report presents the sample, variable definitions and four analysis modules. Charts read aggregate results from `static/data/report.json`.

## Local preview

From the repository root, with the Python environment activated:

```bash
python -m http.server 8787 --directory app
```

Open <http://127.0.0.1:8787/> for Chinese or <http://127.0.0.1:8787/en.html> for English.

## Update results

After the complete analysis has generated a run directory:

```bash
python app/build_report_data.py --run-dir figures/runs/run-YYYYMMDD-HHMMSS
```

The builder updates the aggregate report JSON. Raw responses, row-level predictions and row-level SHAP values are not served as report assets.

Check that tables, charts and both language versions use the same values before publishing. Complete run records are stored in the local results directory.

## Deployment

`.github/workflows/pages.yml` publishes `app/` to [GitHub Pages](https://yemyu.github.io/ev-purchase-intention/) after a push to `main`.

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the chart library license.
