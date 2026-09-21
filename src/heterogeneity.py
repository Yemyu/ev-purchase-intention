"""Supplementary heterogeneity analysis for the EV purchase-intention project.

The old implementation compared a pooled likelihood with a sum of separate
 group likelihoods. Those likelihoods were not nested (and the reported
 degrees of freedom did not match the fitted models), so the resulting LR test
 was not interpretable. This module uses one common sample and two genuinely
 nested ordered-logit models for each demographic variable:

 * restricted: core variables, fixed controls, and group main effects;
 * unrestricted: the restricted model plus ``tech_trust`` and
   ``perceived_value`` by group interaction terms.

The public ``load_data`` and ``analyze_heterogeneity`` functions retain the
interfaces used by ``main.py`` and by the original notebook. Group labels are
kept as generic category labels; no unverified conversion of an age or income
code into a real-world range is made here.
"""

from __future__ import annotations

import warnings
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.miscmodels.ordinal_model import OrderedModel


DATA_PATH = "data/raw/data.csv"

Q_COLS = {
    "Y": "21.您愿意为智能驾驶功能支付溢价?",
    "tech_trust_q1": "15.您认为智能驾驶功能对新能源汽车很重要?",
    "tech_trust_q2": "16.您认为智能驾驶功能可以提高驾驶安全性?",
    "tech_trust_q3": "17.您认为智能驾驶功能可以减轻驾驶疲劳?",
    "value_q1": "22.您愿意为智能驾驶的自适应巡航功能影响购买意愿?",
    "value_q2": "23.您愿意为智能驾驶的车道保持辅助功能影响购买意愿?",
    "value_q3": "24.您愿意为智能驾驶的自动泊车功能影响购买意愿?",
    "value_q4": "25.您愿意为智能驾驶的交通拥堵辅助功能影响购买意愿?",
    "gender": "1.您的性别是?",
    "age": "2.您的年龄是?",
    "education": "4.您的最高学历是?",
    "income": "6.您的月收入范围是?",
    "driving_exp": "9.您的驾龄是?",
    "driving_freq": "12.您每周驾驶的频率是?",
}
# Names retained by the original module for callers that import ``Q_COLS``.
Q_COLS["perceived_value"] = Q_COLS["value_q1"]

CORE_VARS = ["tech_trust", "perceived_value"]
CONTROL_VARS = ["gender", "age", "education", "income", "driving_exp", "driving_freq"]
LEGACY_CONTROL_VARS = ["age", "income", "driving_exp"]
GROUP_VARS = ["gender_gp", "age_gp", "income_gp", "exp_gp", "freq_gp"]


def _number(value: Any) -> Any:
    """Convert a survey column to numeric without turning bad values into 0."""

    return pd.to_numeric(value, errors="coerce")


def _generic_group_labels(series: pd.Series, name: str) -> pd.Series:
    """Return stable labels such as ``age_level_1`` without semantic claims."""

    numeric = _number(series)
    out = pd.Series(pd.NA, index=series.index, dtype="object")
    valid = numeric.notna()
    out.loc[valid] = numeric.loc[valid].map(
        lambda x: f"{name}_level_{int(x) if float(x).is_integer() else x}"
    )
    other = (~valid) & series.notna()
    out.loc[other] = series.loc[other].astype(str).map(lambda x: f"{name}_value_{x}")
    return out


def load_data(data_path: str = DATA_PATH) -> pd.DataFrame:
    """Load raw survey data and construct the primary analysis variables.

    ``tech_trust`` is the pre-specified two-item proxy (Q15/Q16), while
    ``perceived_value`` is the four-item function-appeal proxy (Q22--Q25).
    Legacy/sensitivity definitions are retained as separate columns for
    traceability and are never silently substituted into the analysis.
    """

    # Prefer the shared schema when this module is imported as part of the
    # project.  It is the single source of truth for questionnaire headers and
    # the primary T/V composites.  The local fallback below keeps direct use of
    # this file possible in an older checkout that predates ``data_schema``.
    try:
        from .data_schema import add_derived_variables, load_raw_data

        raw = load_raw_data(data_path)
        df = add_derived_variables(
            raw,
            specification="primary",
            include_question_columns=True,
            include_all_specifications=True,
        )
        df["tech_trust_legacy"] = df["T_legacy"]
        df["tech_trust_sensitivity"] = df["T_sensitivity"]
        df["perceived_value_legacy"] = df["V_legacy"]
        # Canonical aliases are already supplied by data_schema, but assign
        # them explicitly to make this module's contract obvious.
        df["tech_trust"] = df["T"]
        df["perceived_value"] = df["V"]
    except (ImportError, ModuleNotFoundError):
        df = pd.read_csv(data_path, encoding="utf-8-sig")
        missing = [column for column in Q_COLS.values() if column not in df.columns]
        if missing:
            raise KeyError(f"Missing required survey columns: {missing}")

        for key, column in Q_COLS.items():
            df[key] = _number(df[column])

        # A composite is formed only when every pre-specified item is present;
        # partial-item averages would otherwise hide the number of excluded
        # rows.
        df["tech_trust"] = df[["tech_trust_q1", "tech_trust_q2"]].mean(axis=1, skipna=False)
        df["tech_trust_sensitivity"] = df[["tech_trust_q1", "tech_trust_q2", "tech_trust_q3"]].mean(axis=1, skipna=False)
        df["tech_trust_legacy"] = df["tech_trust"]
        value_items = ["value_q1", "value_q2", "value_q3", "value_q4"]
        df["perceived_value"] = df[value_items].mean(axis=1, skipna=False)
        df["perceived_value_legacy"] = df["value_q1"]

    # Group labels do not infer real-world age, income, or year ranges.  The
    # raw category codes remain available in the frame for auditing.
    for variable, label in [
        ("gender", "gender"),
        ("age", "age"),
        ("income", "income"),
        ("driving_exp", "driving_exp"),
        ("driving_freq", "driving_freq"),
    ]:
        if variable not in df.columns:
            raise KeyError(f"Missing control variable from shared schema: {variable}")
        df[variable] = _number(df[variable])

    df["gender_gp"] = _generic_group_labels(df["gender"], "gender")
    df["age_gp"] = _generic_group_labels(df["age"], "age")
    df["income_gp"] = _generic_group_labels(df["income"], "income")
    df["exp_gp"] = _generic_group_labels(df["driving_exp"], "driving_exp")
    df["freq_gp"] = _generic_group_labels(df["driving_freq"], "driving_freq")
    return df


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


def lr_test(llf_full: float, llf_restricted: float, df_diff: int) -> Tuple[float, float]:
    """Return LR statistic and chi-square p-value for nested models."""

    try:
        degrees = int(df_diff)
    except (TypeError, ValueError, OverflowError):
        return np.nan, np.nan
    try:
        finite_llf = bool(np.isfinite(llf_full) and np.isfinite(llf_restricted))
    except TypeError:
        finite_llf = False
    if not finite_llf or degrees <= 0:
        return np.nan, np.nan
    statistic = float(2.0 * (llf_full - llf_restricted))
    if statistic < -1e-7:
        return statistic, np.nan
    statistic = max(0.0, statistic)
    return statistic, float(stats.chi2.sf(statistic, degrees))


def _holm_adjust(p_values: Sequence[float]) -> np.ndarray:
    """Holm step-down adjustment, preserving NaN for failed comparisons."""

    values = np.asarray(p_values, dtype=float)
    adjusted = np.full(values.shape, np.nan, dtype=float)
    valid = np.flatnonzero(np.isfinite(values))
    if not len(valid):
        return adjusted
    order = valid[np.argsort(values[valid], kind="mergesort")]
    m = len(order)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, (m - rank) * values[index])
        adjusted[index] = min(1.0, running)
    return adjusted


def _fit_ologit(y: Sequence[float], X: pd.DataFrame, maxiter: int = 1000):
    """Fit one ordered-logit model and return ``(result, diagnostics)``."""

    diagnostics: Dict[str, Any] = {"converged": False, "error": None}
    try:
        if X.shape[1] == 0:
            raise ValueError("No identifiable predictor columns remain")
        model = OrderedModel(np.asarray(y), X.astype(float), distr="logit")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = model.fit(method="bfgs", maxiter=maxiter, disp=False)
        retvals = getattr(result, "mle_retvals", {}) or {}
        diagnostics["converged"] = bool(retvals.get("converged", True))
        diagnostics["iterations"] = retvals.get("iterations", retvals.get("fcalls", np.nan))
        diagnostics["llf"] = float(result.llf)
        if not diagnostics["converged"]:
            diagnostics["error"] = "optimizer did not report convergence"
        return result, diagnostics
    except Exception as exc:
        diagnostics["error"] = f"{type(exc).__name__}: {exc}"
        return None, diagnostics


def _drop_duplicate_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Remove exact duplicate columns while keeping the first name."""

    if frame.shape[1] <= 1:
        return frame
    keep: List[str] = []
    arrays: List[np.ndarray] = []
    for column in frame.columns:
        values = frame[column].to_numpy(dtype=float)
        if not any(np.array_equal(values, old) for old in arrays):
            keep.append(column)
            arrays.append(values)
    return frame.loc[:, keep]


def _drop_constant_columns(frame: pd.DataFrame) -> pd.DataFrame:
    keep = [column for column in frame.columns if frame[column].nunique(dropna=False) > 1]
    return frame.loc[:, keep]


def _select_independent_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Keep a deterministic maximal-rank subset of a design matrix."""

    selected: List[str] = []
    rank = 0
    for column in frame.columns:
        candidate = frame.loc[:, selected + [column]]
        candidate_rank = _matrix_rank(candidate)
        if candidate_rank > rank:
            selected.append(column)
            rank = candidate_rank
    return frame.loc[:, selected]


def _matrix_rank(frame: pd.DataFrame) -> int:
    if frame.shape[1] == 0 or frame.shape[0] == 0:
        return 0
    return int(np.linalg.matrix_rank(frame.to_numpy(dtype=float)))


def _dummy_code(series: pd.Series, name: str) -> pd.DataFrame:
    values = series.astype(str)
    # Use a deterministic reference category (the lexical first code/label)
    # instead of whichever level happens to occur in the first row.
    levels = sorted(pd.unique(values).tolist())
    if len(levels) <= 1:
        return pd.DataFrame(index=series.index)
    # ``pd.get_dummies(Categorical(...))`` returns a fresh RangeIndex.  Restore
    # the source index so that all design blocks align after rows with missing
    # data have been removed.
    dummy = pd.get_dummies(
        pd.Categorical(values, categories=levels),
        prefix=name,
        drop_first=True,
        dtype=float,
    )
    dummy.index = series.index
    return dummy


def _nested_design(
    df: pd.DataFrame,
    y_var: str,
    x_vars: Sequence[str],
    control_vars: Sequence[str],
    group_var: str,
) -> Dict[str, Any]:
    required = [y_var, *x_vars, *control_vars, group_var]
    absent = [column for column in required if column not in df.columns]
    if absent:
        raise KeyError(f"Missing variables for heterogeneity model: {absent}")

    valid = df[required].notna().all(axis=1)
    work = df.loc[valid, required].copy()
    work[y_var] = _number(work[y_var])
    for variable in x_vars:
        work[variable] = _number(work[variable])
    valid_numeric = work[[y_var, *x_vars]].notna().all(axis=1)
    work = work.loc[valid_numeric].copy()
    if work.empty:
        raise ValueError("No complete observations for this group comparison")

    main = work.loc[:, list(x_vars)].astype(float)
    controls = [_dummy_code(work[variable], variable) for variable in control_vars]
    control_frame = pd.concat(controls, axis=1) if controls else pd.DataFrame(index=work.index)
    group_frame = _dummy_code(work[group_var], group_var)

    restricted = pd.concat([main, control_frame, group_frame], axis=1)
    restricted = _drop_duplicate_columns(restricted)
    restricted = _drop_constant_columns(restricted)
    restricted = _select_independent_columns(restricted)

    interactions: List[pd.Series] = []
    for variable in x_vars:
        for group_column in group_frame.columns:
            interactions.append(
                pd.Series(
                    main[variable].to_numpy() * group_frame[group_column].to_numpy(),
                    index=work.index,
                    name=f"{variable}:{group_column}",
                )
            )
    interaction_frame = pd.concat(interactions, axis=1) if interactions else pd.DataFrame(index=work.index)
    full = pd.concat([restricted, interaction_frame], axis=1)
    full = _drop_duplicate_columns(full)
    full = _drop_constant_columns(full)
    full = _select_independent_columns(full)

    levels = sorted(pd.unique(work[group_var]).tolist())
    return {
        "y": work[y_var].to_numpy(dtype=float),
        "restricted": restricted.astype(float),
        "full": full.astype(float),
        "group_frame": group_frame.astype(float),
        "group_values": levels,
        "group_series": work[group_var],
        "n_obs": int(len(work)),
        "n_dropped": int(len(df) - len(work)),
        "rank_restricted": _matrix_rank(restricted),
        "rank_full": _matrix_rank(full),
        "x_vars": list(x_vars),
    }


def _group_slopes(result: Any, design: Mapping[str, Any]) -> Dict[Any, Dict[str, float]]:
    """Recover reference-group and interaction slopes for readable output."""

    raw_params = getattr(result, "params", pd.Series(dtype=float))
    if isinstance(raw_params, pd.Series):
        params = raw_params
    else:
        values = np.asarray(raw_params, dtype=float).reshape(-1)
        names = list(getattr(getattr(result, "model", None), "exog_names", []))
        if len(names) != len(values):
            names = list(getattr(getattr(result, "model", None), "param_names", []))
        if len(names) != len(values):
            # Slope extraction is a presentation aid only.  The LR result uses
            # the fitted likelihood directly; retain numeric positions if a
            # statsmodels version does not expose parameter names.
            names = list(range(len(values)))
        params = pd.Series(values, index=names)
    groups = design["group_values"]
    group_frame = design["group_frame"]
    output: Dict[Any, Dict[str, float]] = {}
    for group_index, group in enumerate(groups):
        slopes: Dict[str, float] = {}
        for variable in design["x_vars"]:
            value = float(params.get(variable, np.nan))
            if group_index > 0:
                dummy_column = group_frame.columns[group_index - 1] if group_index - 1 < len(group_frame.columns) else None
                interaction_name = f"{variable}:{dummy_column}" if dummy_column else ""
                value += float(params.get(interaction_name, 0.0))
            slopes[variable] = value
        output[group] = slopes
    return output


def analyze_group(
    df: pd.DataFrame,
    group_var: str,
    y_var: str = "Y",
    x_vars: Optional[Sequence[str]] = None,
    control_vars: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Run one nested ordered-logit interaction test."""

    x_vars = list(CORE_VARS if x_vars is None else x_vars)
    if control_vars is None:
        # New schema frames contain all six fixed controls.  The fallback keeps
        # the old notebook usable when it passes a small hand-built frame with
        # only the three controls used by the former implementation.
        control_vars = (
            list(CONTROL_VARS)
            if all(variable in df.columns for variable in CONTROL_VARS)
            else [variable for variable in LEGACY_CONTROL_VARS if variable in df.columns]
        )
    else:
        control_vars = list(control_vars)
    base: Dict[str, Any] = {
        "group_var": group_var,
        "groups": [],
        "group_counts": {},
        "group_coefs": {},
        "group_slopes": {},
        "n_groups": 0,
        "n_obs": 0,
        "n_dropped": 0,
        "df_diff": np.nan,
        "df": np.nan,
        "lr_stat": np.nan,
        "lr_pvalue": np.nan,
        "lr_pvalue_holm": np.nan,
        "p_raw": np.nan,
        "p_holm": np.nan,
        "status": "failed",
        "converged_restricted": False,
        "converged_unrestricted": False,
        "error": None,
        "x_vars": x_vars,
        "control_vars": control_vars,
    }
    try:
        design = _nested_design(df, y_var, x_vars, control_vars, group_var)
        groups = design["group_values"]
        base.update(
            {
                "groups": list(groups),
                "group_counts": design["group_series"].value_counts(sort=False).to_dict(),
                "n_groups": len(groups),
                "n_obs": design["n_obs"],
                "n_dropped": design["n_dropped"],
                "reference_group": groups[0] if groups else None,
                "restricted_columns": list(design["restricted"].columns),
                "unrestricted_columns": list(design["full"].columns),
                "rank_restricted": design["rank_restricted"],
                "rank_unrestricted": design["rank_full"],
            }
        )
        if len(groups) < 2:
            base["status"] = "insufficient_groups"
            base["error"] = "At least two observed group levels are required"
            return base

        restricted_result, restricted_diag = _fit_ologit(design["y"], design["restricted"])
        unrestricted_result, unrestricted_diag = _fit_ologit(design["y"], design["full"])
        base["converged_restricted"] = restricted_diag["converged"]
        base["converged_unrestricted"] = unrestricted_diag["converged"]
        base["restricted_diagnostics"] = restricted_diag
        base["unrestricted_diagnostics"] = unrestricted_diag
        if restricted_result is None or unrestricted_result is None:
            base["error"] = "; ".join(
                error for error in [restricted_diag.get("error"), unrestricted_diag.get("error")] if error
            )
            return base
        if not (restricted_diag["converged"] and unrestricted_diag["converged"]):
            base["error"] = "Both nested models must converge before LR inference"
            return base

        df_diff = int(max(0, design["rank_full"] - design["rank_restricted"]))
        lr_statistic, p_value = lr_test(unrestricted_result.llf, restricted_result.llf, df_diff)
        base.update(
            {
                "df_diff": df_diff,
                "df": df_diff,
                "lr_stat": lr_statistic,
                "lr_pvalue": p_value,
                "p_raw": p_value,
                "restricted_llf": float(restricted_result.llf),
                "unrestricted_llf": float(unrestricted_result.llf),
                "restricted_n_params": int(len(restricted_result.params)),
                "unrestricted_n_params": int(len(unrestricted_result.params)),
                "group_slopes": _group_slopes(unrestricted_result, design),
                "status": "ok" if np.isfinite(p_value) else "invalid_lr",
            }
        )
        first_x = x_vars[0] if x_vars else None
        base["group_coefs"] = {
            group: slopes.get(first_x, np.nan) for group, slopes in base["group_slopes"].items()
        }
        return base
    except Exception as exc:
        base["error"] = f"{type(exc).__name__}: {exc}"
        return base


def heterogeneity_results_table(results: Sequence[Mapping[str, Any]]) -> pd.DataFrame:
    """Convert structured comparison results to a compact, saveable table."""

    rows = []
    for result in results:
        rows.append(
            {
                "group_var": result.get("group_var"),
                "n_obs": result.get("n_obs"),
                "n_groups": result.get("n_groups"),
                "df_diff": result.get("df_diff"),
                "lr_stat": result.get("lr_stat"),
                "p_raw": result.get("lr_pvalue"),
                "p_holm": result.get("lr_pvalue_holm"),
                "status": result.get("status"),
                "error": result.get("error"),
            }
        )
    return pd.DataFrame(rows)


def analyze_heterogeneity(
    df: pd.DataFrame,
    group_vars: Optional[Sequence[str]] = None,
) -> List[Dict[str, Any]]:
    """Run all configured demographic comparisons and apply Holm correction."""

    available = [
        group
        for group in (list(GROUP_VARS) if group_vars is None else list(group_vars))
        if group in df.columns
    ]
    print("=" * 55)
    print("Heterogeneity Analysis (nested ordered-logit LR tests)")
    print("=" * 55)

    results: List[Dict[str, Any]] = [analyze_group(df, group) for group in available]
    adjusted = _holm_adjust([result.get("lr_pvalue", np.nan) for result in results])
    for result, p_adjusted in zip(results, adjusted):
        result["lr_pvalue_holm"] = float(p_adjusted) if np.isfinite(p_adjusted) else np.nan
        result["p_holm"] = result["lr_pvalue_holm"]

    for result in results:
        raw = result.get("lr_pvalue", np.nan)
        adjusted_p = result.get("lr_pvalue_holm", np.nan)
        if np.isfinite(raw) and np.isfinite(adjusted_p):
            print(
                f"\n{result['group_var']}: N={result['n_obs']}, groups={result['n_groups']}, "
                f"LR chi2({int(result['df_diff'])})={result['lr_stat']:.3f}, "
                f"p={raw:.4f}{p_stars(raw)}, Holm p={adjusted_p:.4f}{p_stars(adjusted_p)}"
            )
        else:
            print(
                f"\n{result['group_var']}: status={result.get('status')}, "
                f"N={result.get('n_obs', 0)}, error={result.get('error')}"
            )
        if result.get("group_slopes"):
            for group, slopes in result["group_slopes"].items():
                formatted = ", ".join(f"{name}={value:.4f}" for name, value in slopes.items())
                print(f"  {group}: {formatted}")
    return results


if __name__ == "__main__":
    data = load_data()
    analyze_heterogeneity(data)
