# EV Purchase Intention

This project studies how recognition of intelligent-driving functions relates
to consumers' willingness to pay a premium for new-energy vehicles. It keeps a
two-part design: an ordered-logit analysis for the economic research question,
followed by out-of-fold machine-learning prediction and SHAP explanation as a
computational complement.

The current implementation is a reproducible project revision. It does not
change the thesis document, and it keeps the old analysis outputs in `figures/`
for traceability. New runs are written to a timestamped directory under
`figures/runs/` and are ignored by Git.

## Data and fixed measurements

The raw survey contains 622 respondents and 67 columns. The CSV includes both
original questionnaire columns and historical dummy or exception-handling
columns. Only the explicit raw questionnaire columns are used by the new
pipeline.

The shared schema in `src/config.py` and `src/data_schema.py` defines three
fixed specifications:

| Specification | Technology proxy | Function-value proxy | Controls |
|---|---|---|---|
| `legacy` | mean(Q15, Q16) | Q22 | original ordinal codes |
| `primary` | mean(Q15, Q16) | mean(Q22, Q23, Q24, Q25) | category dummies |
| `sensitivity` | mean(Q15, Q16, Q17) | mean(Q22, Q23, Q24, Q25) | category dummies |

The outcome is Q21, willingness to pay a premium, on a 1–5 ordered scale. Q18
and Q19 are the two single-item exploratory mediators. The primary specification
is fixed before fitting; it is not selected because it produces a smaller
p-value or a higher score. The legacy specification remains so that the old
project can be traced, and the sensitivity specification shows the effect of
including Q17.

The two-item technology measure is a proxy for importance and safety
recognition. The four-item measure is a proxy for recognition of the value of
specific assisted-driving functions. They are not presented as validated,
complete psychological scales. The audit records item missingness, item
correlations, and Cronbach's alpha as descriptive diagnostics.

## Analyses

### Ordered logit

The main analysis fits Q21 on the two core proxies, then adds the fixed six
background controls. It reports coefficients, odds ratios, confidence intervals,
fit statistics, convergence information, and an auxiliary VIF calculation with
an intercept. The results are conditional associations in cross-sectional
survey data.

### Exploratory indirect paths

Five predeclared paths are retained:

- technology proxy → driving pleasure → willingness to pay
- technology proxy → travel efficiency → willingness to pay
- function-value proxy → driving pleasure → willingness to pay
- function-value proxy → travel efficiency → willingness to pay
- technology proxy → function-value proxy → willingness to pay

Each path uses respondent-level OLS equations with the fixed controls and 5,000
bootstrap resamples. The output reports the path coefficients and a bootstrap
interval. These are exploratory indirect associations; they are not multiplied
with ordered-logit coefficients and are not interpreted as causal mediation or
as a percentage of a causal effect.

### Heterogeneity

Demographic differences are a supplementary analysis. For each fixed grouping,
the restricted and unrestricted ordered-logit models are genuinely nested. The
unrestricted model adds technology and value proxy interactions with group
dummies. The likelihood-ratio degrees of freedom are based on the actual design
rank, and raw p-values are accompanied by Holm-adjusted values.

### Machine learning and SHAP

The pipeline uses the same five stratified folds for a majority-class baseline,
ordered logit, and random forest. It compares controls only, controls plus the
two core proxies, and the extended set that also includes Q18 and Q19. It
reports accuracy, macro-F1, quadratic weighted kappa, ordinal MAE, fold-level
metrics, out-of-fold predictions, and confusion matrices.

SHAP is computed on held-out folds for the extended random forest. When the
installed SHAP version supports it, the explanation target is the probability
of a high willingness-to-pay response (`Y >= 4`). Any fallback to raw-output
SHAP is recorded in `ml_run_metadata.json`. SHAP is a predictive explanation;
it is not a causal effect or an independent confirmation of the ordered-logit
model.

## Run locally

Use the project virtual environment for dependencies:

```bash
python3 -m venv .venv
uv pip install --offline --python .venv/bin/python -r requirements.txt
```

If the local package cache is unavailable, install `requirements.txt` through
your normal package mirror inside `.venv`.

Run an audit first:

```bash
.venv/bin/python main.py --analysis audit
```

Run one stage:

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

For a quick functional run of the mediation code, reduce the bootstrap count
explicitly, for example `--analysis mediation --bootstrap-iterations 50`.
The complete run uses 5,000 iterations. Every run records the data SHA256,
mapping manifest, random seed, Python environment, Git state, sample counts,
and output files.

## Project structure

```text
src/config.py             fixed questionnaire mapping and model specifications
src/data_schema.py        data audit, composites, and control encoding
src/ordered_logit.py      ordered-logit associations and VIF
src/mediation.py          five exploratory bootstrap paths
src/heterogeneity.py      nested interaction LR tests
src/ml_shap.py            out-of-fold prediction and SHAP
main.py                   command-line runner and run metadata
data/raw/data.csv         survey data used by the local project
figures/                  historical project outputs
figures/runs/             ignored timestamped outputs from the new pipeline
IMPLEMENTATION_PLAN.md    fixed design decisions and acceptance rules
```

The GitHub repository is private at
https://github.com/Yemyu/ev-purchase-intention.
