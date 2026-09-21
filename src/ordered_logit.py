"""Primary ordered-logit associations for the EV purchase-intention project.

The outcome is the five-level willingness-to-pay item (Q21). The model is fit
with and without the fixed background controls. Results are conditional
associations; this module does not turn an observational coefficient into a
causal claim.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.miscmodels.ordinal_model import OrderedModel
from statsmodels.stats.outliers_influence import variance_inflation_factor

from .config import DEFAULT_DATA_PATH
from .data_schema import build_analysis_frame, load_raw_data


DATA_PATH = str(DEFAULT_DATA_PATH)
CONTROL_PREFIX = "control_"


def load_data(data_path: str | Path = DATA_PATH, specification: str = "primary") -> pd.DataFrame:
    """Load one explicit specification through the shared schema."""

    return build_analysis_frame(load_raw_data(data_path), specification=specification)


def p_stars(p: float) -> str:
    if p is None or not np.isfinite(p):
        return ""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    if p < 0.1:
        return "+"
    return ""


def _control_columns(frame: pd.DataFrame) -> list[str]:
    # A configured level can be absent in a realized sample (Q6 level 5 is
    # absent here). Such all-zero dummy columns are not identifiable and must
    # not enter the ordered model or VIF calculation.
    encoded = [
        str(c)
        for c in frame.columns
        if str(c).startswith(CONTROL_PREFIX)
        and frame[c].dropna().nunique() > 1
    ]
    if encoded:
        return encoded
    return [
        name for name in ("gender", "age", "education", "income", "driving_exp", "driving_freq")
        if name in frame.columns and frame[name].dropna().nunique() > 1
    ]


def _complete_frame(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    required = ["Y", *columns]
    work = frame.loc[:, required].apply(pd.to_numeric, errors="coerce").dropna()
    return work[work["Y"].between(1, 5)]


def run_vif_test(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Compute auxiliary OLS VIFs with a constant included in the design."""

    x = frame.loc[:, columns].astype(float)
    design = np.column_stack([np.ones(len(x)), x.to_numpy()])
    rows: list[dict[str, Any]] = []
    for i, name in enumerate(columns, start=1):
        try:
            value = float(variance_inflation_factor(design, i))
        except Exception:
            value = np.nan
        rows.append({"variable": name, "vif": value})
    return pd.DataFrame(rows)


def _fit(y: pd.Series, x: pd.DataFrame):
    if x.empty or x.shape[1] == 0:
        raise ValueError("No predictors remain after schema construction")
    model = OrderedModel(y.astype(int).to_numpy(), x.astype(float), distr="logit")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = model.fit(method="bfgs", maxiter=1000, disp=False)
    retvals = getattr(result, "mle_retvals", {}) or {}
    return result, {
        "converged": bool(retvals.get("converged", True)),
        "iterations": retvals.get("iterations", retvals.get("fcalls")),
        "llf": float(result.llf),
        "aic": float(result.aic),
        "bic": float(result.bic),
        "prsquared": float(getattr(result, "prsquared", np.nan)),
    }


def _result_rows(result: Any, model_name: str, specification: str, n_obs: int) -> list[dict[str, Any]]:
    names = list(getattr(result.model, "exog_names", []))
    params = np.asarray(result.params, dtype=float)
    pvalues = np.asarray(result.pvalues, dtype=float)
    bse = np.asarray(result.bse, dtype=float)
    conf = np.asarray(result.conf_int(), dtype=float)
    rows = []
    for i, name in enumerate(names):
        if i >= len(params):
            continue
        term = str(name)
        rows.append(
            {
                "specification": specification,
                "model": model_name,
                "term": term,
                "coefficient": float(params[i]),
                "odds_ratio": float(np.exp(params[i])) if term in {"T", "V"} else np.nan,
                "std_error": float(bse[i]),
                "p_value": float(pvalues[i]),
                "ci_low": float(conf[i, 0]),
                "ci_high": float(conf[i, 1]),
                "n_obs": n_obs,
                "term_type": "predictor" if term in {"T", "V"} or term.startswith(CONTROL_PREFIX) else "threshold",
            }
        )
    return rows


def fit_specification(frame: pd.DataFrame, specification: str) -> dict[str, Any]:
    """Fit core and controlled ordered-logit models for one specification."""

    controls = _control_columns(frame)
    model_defs = {"core": ["T", "V"], "controlled": ["T", "V", *controls]}
    output: dict[str, Any] = {"specification": specification, "models": {}, "vif": pd.DataFrame()}
    for model_name, predictors in model_defs.items():
        work = _complete_frame(frame, predictors)
        result, diagnostics = _fit(work["Y"], work[predictors])
        output["models"][model_name] = {
            "result": result,
            "diagnostics": diagnostics,
            "rows": _result_rows(result, model_name, specification, len(work)),
            "predictors": predictors,
        }
        if model_name == "controlled":
            output["vif"] = run_vif_test(work, predictors)
    return output


def _save_plot(rows: pd.DataFrame, output_dir: Path) -> None:
    core = rows[(rows["model"] == "controlled") & (rows["term"].isin(["T", "V"]))]
    if core.empty:
        return
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.barh(core["term"], core["odds_ratio"], color=["#2f6f9f", "#6baed6"])
    ax.axvline(1, color="gray", linestyle="--", linewidth=1)
    ax.set_xlabel("Odds ratio")
    ax.set_title("Core associations in the controlled ordered-logit model")
    fig.tight_layout()
    fig.savefig(output_dir / "ordered_logit_odds_ratios.png", dpi=160, facecolor="white")
    plt.close(fig)


def run_ordered_logit_analysis(
    df: pd.DataFrame | None = None,
    output_dir: str | Path = "figures/runs",
    *,
    data_path: str | Path = DATA_PATH,
    specifications: tuple[str, ...] = ("primary", "sensitivity", "legacy"),
) -> dict[str, Any]:
    """Run declared specifications and save structured CSV/JSON outputs."""

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    all_rows: list[dict[str, Any]] = []
    diagnostics: dict[str, Any] = {}
    for specification in specifications:
        frame = df if df is not None and df.attrs.get("schema_specification") == specification else load_data(data_path, specification)
        fitted = fit_specification(frame, specification)
        diagnostics[specification] = {model: info["diagnostics"] for model, info in fitted["models"].items()}
        all_rows.extend(row for info in fitted["models"].values() for row in info["rows"])
        fitted["vif"].to_csv(out / f"vif_{specification}.csv", index=False)
    rows = pd.DataFrame(all_rows)
    rows.to_csv(out / "ordered_logit_coefficients.csv", index=False)
    (out / "ordered_logit_diagnostics.json").write_text(json.dumps(diagnostics, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    _save_plot(rows, out)
    return {"coefficients": rows, "diagnostics": diagnostics, "output_dir": str(out)}


if __name__ == "__main__":
    run_ordered_logit_analysis()
