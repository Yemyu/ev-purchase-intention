<p align="center">
  <a href="README.md">中文</a> · <a href="README.en.md">English</a>
</p>

<h1 align="center">Driver-assistance features and willingness to pay more for an EV</h1>

<p align="center">Econometric analysis and machine learning using 622 consumer survey responses</p>

<p align="center">
  <a href="notebooks/01_ev_purchase_intention_en.ipynb">Analysis Notebook</a> ·
  <a href="https://yemyu.github.io/ev-purchase-intention/en.html">Research report</a> ·
  <a href="https://yemyu.github.io/ev-purchase-intention/en.html#ml">Results dashboard</a>
</p>

---

This project examines how consumers’ ratings of driving safety and feature value relate to willingness to pay a premium, and compares predictions from ordered logit and random forest models.

## Research question

Using 622 survey responses, the project studies whether recognition of intelligent-driving functions is associated with consumers' willingness to pay a premium for new-energy vehicles. It also checks:

1. whether technology importance and safety recognition (`T`) are positively associated with willingness to pay (`Y`);
2. whether perceived value of concrete assisted-driving functions (`V`) is positively associated with `Y`;
3. whether driving pleasure (`M1`) and travel efficiency (`M2`) form exploratory indirect paths;
4. whether the associations vary across demographic groups; and
5. whether machine learning can reproduce ordinal purchase-intention information out of fold and which features contribute to predictions.

The estimand is a **conditional association and predictive performance in a cross-sectional survey**, not a causal effect.

## Design at a glance

```text
Raw questionnaire CSV
    │
    ├─ explicit question mapping, missing/range/duplicate audit
    ├─ ordered logit: Y ~ T + V + fixed controls        ← primary result
    ├─ bootstrap paths: T/V → M1/M2 → Y                ← exploratory
    ├─ nested LR tests + Holm correction                ← heterogeneity
    └─ five-fold out-of-fold prediction + SHAP          ← computational complement
```

Question numbers, variable definitions, controls, and missing-data rules are centralized in [`src/config.py`](src/config.py) and [`src/data_schema.py`](src/data_schema.py). The current code does not automatically select items by p-values or scores. Item selection has a history of exploration on these data; fixed code specifications do not constitute preregistration or remove prior selection effects.

## Data and measurements

The repository is currently public and keeps the 622-row, 67-column raw survey CSV for project reproduction, as authorized by the project owner. The report page loads aggregate JSON only; the analysis resolves explicit raw question headers and never passes historical dummy or exception-handling columns into a model.

| Symbol | Meaning | Primary specification |
|---|---|---|
| `Y` | Willingness to pay a premium for intelligent-driving functions | Q21, ordinal 1–5 |
| `T` | Technology-importance and safety recognition proxy | `mean(Q15, Q16)` |
| `V` | Value recognition for concrete assisted-driving functions | `mean(Q22, Q23, Q24, Q25)` |
| `M1` | Recognition of improved driving pleasure | Q18 |
| `M2` | Recognition of improved travel efficiency | Q19 |

Three fixed specifications are retained for traceability:

| Specification | T | V | Control encoding | Purpose |
|---|---|---|---|---|
| `primary` | mean(Q15, Q16) | mean(Q22–Q25) | categorical dummies | current main specification |
| `sensitivity` | mean(Q15–Q17) | mean(Q22–Q25) | categorical dummies | adds fatigue-relief recognition |
| `legacy` | mean(Q15, Q16) | Q22 | original ordinal codes | traceability to the original project |

T and V are project-defined **proxies**, not externally validated psychological scales. The audit records missingness, response ranges, item correlations, and Cronbach's alpha as descriptive diagnostics; it does not delete items after inspecting reliability or significance.

See the [bilingual data dictionary](data/README.en.md) for exact questionnaire text, coding, missing-data policy, and privacy notes.

## Analysis modules

### Data audit

`main.py --analysis audit` records sample size, duplicate rows, question resolution, 1–5 range checks, item missingness, control categories, historical processing columns, and composite diagnostics. The audit documents the data; it does not silently repair the source CSV.

### Ordered logit

The primary model treats Q21 as an ordered outcome and includes T, V, and six fixed background controls. Outputs include coefficients, odds ratios, confidence intervals, p-values, sample counts, convergence status, and an auxiliary VIF calculation with an intercept. Interpret results as conditional associations in the observed survey.

### Exploratory bootstrap paths

Five paths are fixed in advance:

- `T → M1 → Y`
- `T → M2 → Y`
- `V → M1 → Y`
- `V → M2 → Y`
- `T → V → Y`

Each uses 5,000 respondent-level bootstrap resamples and records valid/failing draws. The mediator equations are exploratory OLS approximations; the results are not causal mediation, not full/partial mediation labels, and not a causal-effect proportion.

### Heterogeneity

Gender, age, income, driving experience, and driving frequency are tested one at a time by comparing genuinely nested ordered-logit models. The unrestricted model adds `T/V × group` interactions. Degrees of freedom use the actual design-matrix rank, and both raw and Holm-adjusted p-values are reported. This module is supplementary and exploratory.

### Machine learning and SHAP

The same five stratified folds compare a majority baseline, ordered logit, and random forest across `controls`, `core` (controls + T/V), and `extended` (also M1/M2). Accuracy, macro-F1, quadratic weighted kappa, ordinal MAE, fold metrics, out-of-fold predictions, and confusion matrices are saved.

SHAP is computed on held-out folds for the extended forest. If the installed SHAP version cannot produce high-intention probability explanations, the raw-output fallback is recorded in `ml_run_metadata.json`. SHAP is predictive feature attribution, not causal evidence.

## Quick start

Install and run dependencies inside the project virtual environment:

```bash
python3 -m venv .venv
uv pip install --offline --python .venv/bin/python -r requirements.txt
```

If the local cache is unavailable, use your normal package mirror inside `.venv`; do not modify the system Python environment.

Run the low-cost audit first:

```bash
.venv/bin/python main.py --analysis audit
```

Run individual modules:

```bash
.venv/bin/python main.py --analysis econometrics
.venv/bin/python main.py --analysis mediation
.venv/bin/python main.py --analysis heterogeneity
.venv/bin/python main.py --analysis ml
```

Run the complete pipeline:

```bash
.venv/bin/python main.py --analysis all
```

The complete run uses 5,000 bootstrap iterations. For a quick functional check, reduce it explicitly, for example `--analysis mediation --bootstrap-iterations 50`.

Every run creates `figures/runs/run-YYYYMMDD-HHMMSS/` and records the data SHA256, mapping manifest, seed, Python environment, Git state, and module outputs. Run directories are ignored by default; submit a separate de-identified summary if reviewers need to inspect results.

## Notebooks

The notebooks are now separated by language:

- [`01_ev_purchase_intention_zh.ipynb`](notebooks/01_ev_purchase_intention_zh.ipynb): Chinese research notes and interpretation;
- [`01_ev_purchase_intention_en.ipynb`](notebooks/01_ev_purchase_intention_en.ipynb): English research notes and interpretation;
- [`notebooks/README.md`](notebooks/README.md): execution order, run-directory selection, and troubleshooting.

Both notebooks call the shared schema and read the saved run outputs. They no longer reproduce the old single-item Q22 definition, single train/test split, or legacy random-forest workflow. They do not start the expensive full pipeline by default; run the CLI first when fresh results are required.

## Why there is a report page instead of an operational dashboard

This repository delivers a reproducible research analysis rather than a continuously monitored operational product. The data are a one-time survey and the meaningful outputs are model tables, intervals, and methodological notes. The current version therefore provides a read-only static report page for the audit, odds ratios, bootstrap intervals, and ML metrics instead of an operational dashboard that would require continuously refreshed data.

The report page is available at <https://yemyu.github.io/ev-purchase-intention/>. It is published from `app/` by the GitHub Pages workflow; the notebooks and complete analysis code remain in the repository.

## Repository layout

```text
src/config.py             fixed question map, specifications, controls, run settings
src/data_schema.py        raw loading, audit, composites, control encoding
src/ordered_logit.py      ordered-logit associations and VIF
src/mediation.py          five exploratory bootstrap paths
src/heterogeneity.py      nested interaction LR tests
src/ml_shap.py            out-of-fold prediction and SHAP
main.py                   CLI entry point and run metadata
notebooks/                bilingual notebooks and navigation
data/README.md            bilingual data dictionary and privacy notes
figures/                  historical figures and local run outputs
IMPLEMENTATION_PLAN.md    locked design, boundaries, and acceptance rules
```

## Scope and privacy

- The survey is cross-sectional, self-reported, and subject to convenience-sampling and common-method limitations.
- T and V are proxies and should not be described as validated scales.
- Results are suitable for a research portfolio and methodological demonstration, not a population-level causal estimate.
- The repository is public and retains the raw survey CSV for this project's reproduction, as authorized by the project owner. The web page does not load row-level data. Do not reuse or redistribute raw responses outside the project without the project owner's authorization.
- The thesis document is not changed here. If it still uses the legacy single-item V definition, document that version boundary explicitly.

## License and citation

Code is released under [`LICENSE`](LICENSE). If you use the survey or analysis design, acknowledge the data collection, variable construction, sample limitations, and repository version.

GitHub repository: <https://github.com/Yemyu/ev-purchase-intention>
