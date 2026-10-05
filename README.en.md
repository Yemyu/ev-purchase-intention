<p align="center">
  <a href="README.md">中文</a> · <a href="README.en.md">English</a>
</p>

<h1 align="center">Driver-assistance features and willingness to pay a premium for an EV</h1>

<p align="center">Econometric analysis and machine learning using 622 consumer survey responses</p>

<p align="center">
  <a href="notebooks/01_ev_purchase_intention_en.ipynb">Analysis Notebook</a> ·
  <a href="https://yemyu.github.io/ev-purchase-intention/en.html">Research report</a>
</p>

---

This project examines how consumers’ perceptions of driver-assistance technology and specific features relate to willingness to pay a premium. It includes ordered logit, exploratory indirect paths, group comparisons, and a prediction comparison between ordered logit and random forest.

## Main findings

| Analysis | Result |
|---|---|
| Ordered logit | After adjustment for six background variables, the odds ratio for technology perceptions T is **2.08** (95% CI: 1.62–2.68), and for perceived feature value V it is **3.83** (2.84–5.16); both p < 0.001 |
| Indirect paths | All five bootstrap 95% intervals are above zero; indirect estimates range from 0.163 to 0.351 |
| Group comparisons | None of the five interaction tests for gender, age, income, driving experience and frequency meets the 0.05 threshold after Holm adjustment |
| Prediction | With T, V, driving pleasure and travel efficiency included, ordered logit has mean five-fold QWK **0.685** and accuracy **54.5%**; random forest scores **0.619** and **53.5%**, respectively |
| SHAP | Perceived feature value, technology perceptions, driving pleasure and travel efficiency rank first to fourth by mean absolute SHAP for the extended forest’s high-willingness probability |

The research report and executed notebooks include the full tables, figures and analysis notes.

## Data and variables

The dataset contains 622 online survey responses. The CSV has 67 columns, including 29 original questionnaire items. Analysis inputs are selected by question number and original header.

| Symbol | Meaning | Construction |
|---|---|---|
| Y | Willingness to pay a premium for driver-assistance features | Q21, ordered categories 1–5 |
| T | Technology perceptions: importance and safety | Mean of Q15 and Q16 |
| V | Perceived feature value: ratings of four assistance features | Mean of Q22–Q25 |
| M1 | Perceived driving pleasure | Q18, single item |
| M2 | Perceived travel efficiency | Q19, single item |

Controls are gender, age, education, income, driving experience and driving frequency, encoded as questionnaire categories. Composites require complete item responses; each model uses complete records for its required variables.

See the [data documentation](data/README.en.md) for questionnaire items, category codes and missing-data rules.

## Four analysis modules

### Ordered logit

The five ordered Y categories are modeled using T, V and six controls. Outputs include coefficients, odds ratios, 95% confidence intervals and p-values. Odds ratios describe the adjusted association for a one-point increase in T or V. The main model uses 622 respondents.

### Exploratory indirect paths

T→M1→Y, T→M2→Y, V→M1→Y, V→M2→Y and T→V→Y are estimated separately. Each path uses OLS equations with controls. Respondents are resampled with replacement 5,000 times to obtain percentile intervals for the coefficient product.

### Group comparisons

For five demographic and driving-history groupings, nested ordered-logit models are compared before and after adding T and V interaction terms. Likelihood-ratio tests are adjusted across the five comparisons using Holm’s method.

### Prediction and SHAP

A majority baseline, ordered logit and random forest use the same five stratified folds with seed 42. Three inputs are compared: background controls, controls plus T/V, and controls plus T/V/M1/M2. Metrics are accuracy, macro-F1, quadratic weighted kappa (QWK) and ordinal MAE. Random forests use 200 trees and maximum depth 6. SHAP explains the extended forest’s P(Y≥4) on each held-out fold and summarizes all 23 input features.

See [analysis methods](docs/METHODS.en.md) for equations, metric definitions and limitations.

## Quick start

The saved notebook outputs and research report can be read directly. Use Python 3.12 to recompute the analysis.

### 1. Clone the repository

```bash
git clone https://github.com/Yemyu/ev-purchase-intention.git
cd ev-purchase-intention
```

### 2. Install dependencies

macOS / Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Windows (PowerShell):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

With the environment activated:

```bash
python -m pip install -r requirements.txt
```

### 3. Run the analysis

```bash
python main.py --analysis audit
python main.py --analysis all
```

`audit` writes data-quality records. `all` generates the complete analysis, including 5,000 bootstrap draws. Results are saved to `figures/runs/run-YYYYMMDD-HHMMSS/`.

Individual modules can also be run:

```bash
python main.py --analysis econometrics
python main.py --analysis mediation
python main.py --analysis heterogeneity
python main.py --analysis ml
```

### 4. Open a notebook

```bash
jupyter lab
```

Open either language version. When executed, the notebook reads the latest complete run directory. See the [notebook guide](notebooks/README.en.md) to select a specific directory.

## Repository layout

```text
main.py              Command-line analysis entry point
src/                 Data processing, econometrics, paths, group tests and prediction
notebooks/           Chinese and English analysis notebooks
app/                 Research report and aggregate data
data/raw/data.csv    Survey data
data/README.en.md    Data dictionary
docs/METHODS.en.md    Analysis methods and limitations
figures/runs/        Locally generated analysis results
archive/             Historical figures and report layout
requirements.txt     Python dependencies
```

See [app/README.en.md](app/README.en.md) for local preview and report updates.

## Limitations

The cross-sectional convenience sample supports associations and predictive results within the survey. Y measures willingness to pay a premium rather than observed purchases. T and V are item composites without external scale validation. V’s questions already refer to purchase intention and are conceptually close to Y.

Items were explored on the same data; the current cross-validation does not include that earlier selection process. The ordered-logit proportional-odds assumption has not been specifically tested. Indirect paths treat ratings as continuous in OLS approximations, and SHAP describes predictive feature attribution.

## Data use and license

The repository contains raw survey responses; the research report uses aggregate data. Reuse or redistribution of survey responses requires the relevant authorization.

The code is released under the [MIT License](LICENSE).
