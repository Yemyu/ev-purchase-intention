# EV Purchase Intention

Investigating how autonomous driving features influence consumers' purchase intention for New Energy Vehicles (NEVs) through survey-based econometric analysis.

## Overview

Based on 622 survey responses collected in China (2024–2025), this project applies **ordered logit regression**, **bootstrap mediation analysis**, **heterogeneity testing**, and **ML + SHAP interpretability** to understand the key drivers behind NEV purchase decisions.

## Key Findings

| Hypothesis | Path | Estimate | Result |
|------------|------|----------|--------|
| H1 | Tech Trust → Purchase Intention | OR=2.77, p<0.001 | Significant |
| H2 | Perceived Value → Purchase Intention | OR=2.20, p<0.001 | Significant |
| H3 | Tech Trust → Enjoyment → Intention | 35% mediation | Partial mediation |
| H4 | Value → Efficiency → Intention | Significant | Partial mediation |

Both technology trust and perceived value are significant predictors of purchase intention, with indirect effects operating through driving enjoyment and travel efficiency.

## Key Improvements

| Issue | Solution | Impact |
|-------|----------|--------|
| Multicollinearity (VIF=22.3) | Selective control strategy | Core variables remain significant |
| Heterogeneous effects | LR test by demographic groups | Identified key segments |
| Non-linear relationships | ML + SHAP validation | Robust results confirmed |

## Data Sources

| Source | Description |
|--------|-------------|
| Survey data | 622 consumers in China (2024–2025) |
| Variables | 39 items: tech trust, perceived value, driving enjoyment, travel efficiency, demographics |
| Location | `data/raw/data.csv` |

## Project Structure

```
ev-purchase-intention/
├── src/
│   ├── ordered_logit.py      # Ordered logit regression + VIF
│   ├── mediation.py          # Bootstrap mediation analysis
│   ├── heterogeneity.py      # Group comparison + LR test
│   └── ml_shap.py           # ML prediction + SHAP
├── notebooks/
│   └── 01_ev_purchase_intention.ipynb
├── figures/                  # Output visualizations
├── data/raw/                 # Raw survey data
├── main.py                   # CLI entry point
├── requirements.txt
├── LICENSE
└── README.md
```

## Quick Start

**Option A — Run locally:**
```bash
git clone https://github.com/Yemyu/ev-purchase-intention.git
cd ev-purchase-intention
pip install -r requirements.txt

# Download data and place in data/raw/
jupyter notebook notebooks/01_ev_purchase_intention.ipynb
```

**Option B — Run on Google Colab:**

Upload `notebooks/01_ev_purchase_intention.ipynb` to [Google Colab](https://colab.research.google.com/), then upload `data/raw/data.csv` via the file panel on the left. No local setup needed.

## Methodology

### 1. Ordered Logit Regression

Custom proportional odds model handling the ordinal nature of purchase intention (1–5 Likert scale). Addresses multicollinearity through selective control variable strategy, reducing VIF from 22.3 to acceptable levels.

### 2. Mediation Analysis (Bootstrap)

Five mediation paths tested using 5,000 bootstrap samples:

- Tech Trust → Driving Enjoyment → Purchase Intention
- Tech Trust → Travel Efficiency → Purchase Intention
- Perceived Value → Driving Enjoyment → Purchase Intention
- Perceived Value → Travel Efficiency → Purchase Intention
- Tech Trust → Perceived Value → Purchase Intention

### 3. Heterogeneity Analysis

LR test for group differences across:

- Age groups (Youth / Middle-aged / Senior)
- Income levels (Low / Middle / High)
- Driving experience (Novice / Experienced / Expert)

### 4. ML + SHAP

Random Forest classifier with SHAP values for model validation and feature interpretability.

## Limitations & Future Work

- **Cross-sectional data**: Causal inference limited; longitudinal tracking of attitude changes would strengthen conclusions
- **Sample scope**: Single country, urban respondents; cross-cultural comparison could extend generalizability
- **Future directions**:
  - Field experiment with EV test drives
  - Integration of revealed preference data
  - Policy variable analysis (subsidies, regulations)

## Tech Stack

Python · pandas · numpy · scipy · statsmodels · scikit-learn · shap · matplotlib · seaborn

## License

[MIT](LICENSE)
