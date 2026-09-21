"""Exploratory respondent-level bootstrap paths.

The outcome is ordinal, so these OLS path decompositions are reported as
exploratory indirect associations. They are not multiplied with ordered-logit
coefficients and are not labelled causal mediation effects.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .config import BOOTSTRAP_ITERATIONS, DEFAULT_DATA_PATH, RANDOM_SEED
from .data_schema import build_analysis_frame, load_raw_data


DATA_PATH = str(DEFAULT_DATA_PATH)
CONTROL_PREFIX = "control_"


def load_data(data_path: str | Path = DATA_PATH, specification: str = "primary") -> pd.DataFrame:
    return build_analysis_frame(load_raw_data(data_path), specification=specification)


def _control_columns(frame: pd.DataFrame) -> list[str]:
    return [
        str(c)
        for c in frame.columns
        if str(c).startswith(CONTROL_PREFIX)
        and frame[c].dropna().nunique() > 1
    ]


def _design(frame: pd.DataFrame, predictors: list[str]) -> np.ndarray:
    return np.column_stack([np.ones(len(frame)), frame[predictors].to_numpy(dtype=float)])


def _ols(y: np.ndarray, x: np.ndarray) -> dict[str, Any]:
    beta, _, rank, singular = np.linalg.lstsq(x, y, rcond=None)
    residual = y - x @ beta
    dof = max(1, len(y) - x.shape[1])
    sigma2 = float(residual @ residual / dof)
    inv = np.linalg.pinv(x.T @ x)
    se = np.sqrt(np.maximum(0.0, sigma2 * np.diag(inv)))
    return {"params": beta, "bse": se, "rank": int(rank), "singular": singular}


def _path_point(data: pd.DataFrame, x: str, mediator: str, controls: list[str]) -> dict[str, float]:
    ra = _ols(data[mediator].to_numpy(float), _design(data, [x, *controls]))
    rc = _ols(data["Y"].to_numpy(float), _design(data, [x, *controls]))
    rb = _ols(data["Y"].to_numpy(float), _design(data, [x, mediator, *controls]))
    a = float(ra["params"][1])
    c = float(rc["params"][1])
    b = float(rb["params"][2])
    c_prime = float(rb["params"][1])
    return {"a": a, "b": b, "c": c, "c_prime": c_prime, "indirect": a * b}


def _bootstrap_indirect(data: pd.DataFrame, x: str, mediator: str, controls: list[str], iterations: int, seed: int) -> tuple[np.ndarray, int]:
    """Bootstrap OLS products using multinomial frequency weights.

    A resampled OLS fit is algebraically identical to a weighted fit on the
    original rows. Computing the small cross-products directly avoids creating
    25,000 temporary DataFrames while preserving the respondent bootstrap.
    """

    rng = np.random.default_rng(seed)
    values = np.full(iterations, np.nan, dtype=float)
    y = data["Y"].to_numpy(float)
    m = data[mediator].to_numpy(float)
    design_a = _design(data, [x, *controls])
    design_b = _design(data, [x, mediator, *controls])
    for iteration in range(iterations):
        index = rng.integers(0, len(data), size=len(data))
        counts = np.bincount(index, minlength=len(data)).astype(float)
        try:
            gram_a = design_a.T @ (counts[:, None] * design_a)
            gram_b = design_b.T @ (counts[:, None] * design_b)
            beta_a = np.linalg.solve(gram_a, design_a.T @ (counts * m))
            beta_b = np.linalg.solve(gram_b, design_b.T @ (counts * y))
            values[iteration] = float(beta_a[1] * beta_b[2])
        except (np.linalg.LinAlgError, ValueError, FloatingPointError):
            continue
    valid = np.isfinite(values)
    return values, int((~valid).sum())


def mediation_path(
    x: str,
    mediator: str,
    data: pd.DataFrame,
    *,
    controls: list[str] | None = None,
    x_name: str | None = None,
    mediator_name: str | None = None,
    iterations: int = BOOTSTRAP_ITERATIONS,
    seed: int = RANDOM_SEED,
) -> dict[str, Any]:
    controls = list(controls or _control_columns(data))
    needed = ["Y", x, mediator, *controls]
    work = data.loc[:, needed].apply(pd.to_numeric, errors="coerce").dropna().reset_index(drop=True)
    if len(work) <= len(controls) + 5:
        raise ValueError(f"Too few complete rows for path {x}->{mediator}: {len(work)}")
    point = _path_point(work, x, mediator, controls)
    bootstrap, failures = _bootstrap_indirect(work, x, mediator, controls, iterations, seed)
    finite = bootstrap[np.isfinite(bootstrap)]
    if not len(finite):
        raise RuntimeError(f"All bootstrap fits failed for path {x}->{mediator}")
    ci_low, ci_high = np.percentile(finite, [2.5, 97.5])
    return {
        "x": x_name or x,
        "mediator": mediator_name or mediator,
        "x_column": x,
        "mediator_column": mediator,
        "n_obs": int(len(work)),
        "a": point["a"],
        "b": point["b"],
        "c_total": point["c"],
        "c_prime": point["c_prime"],
        "indirect": point["indirect"],
        "ci_low": float(ci_low),
        "ci_high": float(ci_high),
        "bootstrap_iterations": int(iterations),
        "bootstrap_valid": int(len(finite)),
        "bootstrap_failures": int(failures),
        "bootstrap_seed": int(seed),
        "bootstrap_values": finite,
    }


def _save_distribution(results: list[dict[str, Any]], output_dir: Path) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(12, 7))
    for index, result in enumerate(results):
        ax = axes.flat[index]
        ax.hist(result["bootstrap_values"], bins=35, color="#377eb8", alpha=0.8)
        ax.axvline(0, color="#d62728", linestyle="--", linewidth=1)
        ax.axvline(result["ci_low"], color="#ff7f00", linestyle=":")
        ax.axvline(result["ci_high"], color="#ff7f00", linestyle=":")
        ax.set_title(f"{result['x']} -> {result['mediator']}", fontsize=9)
        ax.set_xlabel("Indirect association")
    axes.flat[-1].axis("off")
    fig.tight_layout()
    fig.savefig(output_dir / "mediation_bootstrap_distributions.png", dpi=160, facecolor="white")
    plt.close(fig)


def run_mediation_analysis(
    df: pd.DataFrame | None = None,
    output_dir: str | Path = "figures/runs",
    *,
    data_path: str | Path = DATA_PATH,
    specification: str = "primary",
    iterations: int = BOOTSTRAP_ITERATIONS,
) -> dict[str, Any]:
    """Run the five pre-declared exploratory paths."""

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    frame = df if df is not None and df.attrs.get("schema_specification") == specification else load_data(data_path, specification)
    paths = [
        ("T", "M1", "Technology proxy", "Driving pleasure"),
        ("T", "M2", "Technology proxy", "Travel efficiency"),
        ("V", "M1", "Function-value proxy", "Driving pleasure"),
        ("V", "M2", "Function-value proxy", "Travel efficiency"),
        ("T", "V", "Technology proxy", "Function-value proxy"),
    ]
    results = [mediation_path(x, m, frame, x_name=xn, mediator_name=mn, iterations=iterations) for x, m, xn, mn in paths]
    table = pd.DataFrame([{k: v for k, v in result.items() if k != "bootstrap_values"} for result in results])
    table.to_csv(out / "mediation_paths.csv", index=False)
    _save_distribution(results, out)
    (out / "mediation_paths.json").write_text(json.dumps([{k: v for k, v in r.items() if k != "bootstrap_values"} for r in results], ensure_ascii=False, indent=2), encoding="utf-8")
    return {"table": table, "results": results, "output_dir": str(out)}


if __name__ == "__main__":
    run_mediation_analysis()
