# Analysis methods

[中文](METHODS.md) · [English](METHODS.en.md) · [Project overview](../README.en.md)

## Data and measurements

The study uses 622 online survey responses. Y is the ordered 1–5 response to Q21 on willingness to pay a premium. Technology perceptions T averages Q15 (importance) and Q16 (safety). Perceived feature value V averages Q22–Q25: adaptive cruise control, lane keeping, parking assistance and traffic-jam assistance. M1 is Q18 (driving pleasure); M2 is Q19 (travel efficiency).

The background controls are gender, age, education, income, driving experience and driving frequency. Categories use reference-group dummies rather than continuous age or income values. Composites require complete item responses, and each analysis uses complete records for its required variables.

See [data documentation](../data/README.en.md) for source wording, code ranges and output files.

## Ordered logit

The main model is:

```text
logit P(Y > k) = βT T + βV V + γ′C − κk,   k = 1, 2, 3, 4
```

C contains category-coded background controls and κ denotes the thresholds. Under proportional odds, coefficients are shared across thresholds. exp(β) is the ratio of the odds of exceeding a threshold for a one-point increase in the predictor, holding other variables constant.

The report presents the adjusted model using the current variable definitions (`specification=primary`, `model=controlled` in the result file). Unadjusted estimates, full coefficients, fitting diagnostics and auxiliary VIF calculations are also saved. The auxiliary VIF regression includes an intercept; ordered logit does not add a constant column.

The T odds ratio is 2.08 (95% CI: 1.62–2.68); V is 3.83 (2.84–5.16). These are conditional associations rather than probability ratios. The proportional-odds assumption has not been specifically tested.

## Exploratory indirect paths

Five paths are estimated separately: T→M1→Y, T→M2→Y, V→M1→Y, V→M2→Y and T→V→Y. Each uses two OLS equations with intercepts and controls:

```text
M = α + aX + δ′C + εM
Y = θ + c′X + bM + η′C + εY
Indirect association = a × b
```

Respondents are resampled with replacement 5,000 times using seed 42. The 95% percentile interval uses the 2.5th and 97.5th percentiles of the product distribution. Each reported path has 5,000 valid estimates.

| Path | a×b | 95% bootstrap interval |
|---|---:|---|
| T→M1→Y | 0.256 | 0.180–0.330 |
| T→M2→Y | 0.180 | 0.100–0.256 |
| V→M1→Y | 0.257 | 0.183–0.332 |
| V→M2→Y | 0.163 | 0.079–0.248 |
| T→V→Y | 0.351 | 0.258–0.438 |

Paths are fitted separately. The first four do not additionally control for the other core perception variable, leaving possible omitted-variable confounding. These are not simultaneous parallel-mediation estimates, and the products cannot be added into an overall contribution. Intervals are per-path intervals rather than simultaneous intervals across all five paths. OLS approximates the ordered ratings as equally spaced, while the cross-sectional data cannot establish temporal ordering.

## Group comparisons

Gender, age, income, driving experience and driving frequency are tested separately. The restricted model includes T, V, the six controls and group main effects; the expanded model adds T-by-group and V-by-group interactions. Both use the same complete sample.

```text
LR = 2 × (logLik expanded − logLik restricted)
```

Degrees of freedom use the actual rank difference between design matrices. LR inference requires convergence of both models. Holm’s method adjusts the five raw p-values.

Gender and age have raw p-values of 0.013 and 0.042, increasing to 0.063 and 0.170 after adjustment. All five adjusted values exceed 0.05, so the sample does not provide adjusted significant evidence of slope differences.

## Prediction comparison

The same five stratified folds (shuffled, seed 42) compare three input sets:

1. Six background controls;
2. Controls plus T and V;
3. Controls plus T, V, M1 and M2.

Each set is evaluated with a majority baseline, ordered logit and random forest. The majority class is determined from the training fold. Forests use 200 trees and maximum depth 6. Training and test samples are separated within each fold. Composites are calculated per respondent, and category encoding follows the declared configuration levels.

| Metric | Meaning |
|---|---|
| Accuracy | Proportion of exact category matches |
| Macro-F1 | Unweighted mean F1 across the five categories |
| QWK | Quadratic weighted kappa, accounting for ordinal error and chance agreement |
| Ordinal MAE | Mean absolute difference between predicted and observed categories |

Reported metrics are fold means. With extended inputs, ordered logit scores QWK 0.685 and accuracy 54.5%; random forest scores 0.619 and 53.5%. These compare performance within the chosen split rather than validate it in an external sample.

An `ok` fold status means no exception was raised. The original prediction pipeline did not separately save optimizer convergence diagnostics for ordered logit.

## SHAP

SHAP explains the extended forest’s predicted probability of high willingness, P(Y≥4). Each fold uses its training data as explainer background and explains its held-out sample. Attributions for category probabilities 4 and 5 are summed, then ranked by mean absolute value.

The chart includes T, V, M1, M2 and encoded background variables, totaling 23 inputs. Mean absolute SHAP measures attribution magnitude, not direction. Perceived feature value, technology perceptions, driving pleasure and travel efficiency rank first to fourth.

## Limitations

- The cross-sectional convenience sample is subject to self-report and common-method bias; willingness to pay does not measure actual purchases.
- T and V are item composites without external scale validation. Internal consistency does not establish construct validity.
- V’s items refer to feature effects on purchase intention and are conceptually close to Y.
- Items were explored on the same data; the current cross-validation does not include that earlier selection process.
- Proportional odds, continuous-rating path approximations and external generalization remain limitations. Optimizer convergence for ordered logit was not separately recorded by fold.
