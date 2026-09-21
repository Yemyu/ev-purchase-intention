"""Out-of-fold ordinal prediction and SHAP explanation.

The comparison uses the same primary sample and the same five stratified
folds for a majority baseline, ordered logit, and random forest.  ML results
describe prediction on held-out respondents; SHAP is a predictive explanation
and is not treated as a causal effect.
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
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, cohen_kappa_score, confusion_matrix, f1_score, mean_absolute_error
from sklearn.model_selection import StratifiedKFold
from statsmodels.miscmodels.ordinal_model import OrderedModel

from .config import CV_FOLDS, DEFAULT_DATA_PATH, RANDOM_SEED
from .data_schema import build_analysis_frame, load_raw_data


DATA_PATH = str(DEFAULT_DATA_PATH)
CONTROL_PREFIX = "control_"
LABELS = np.arange(1, 6)


def load_data(data_path: str | Path = DATA_PATH, specification: str = "primary") -> pd.DataFrame:
    return build_analysis_frame(load_raw_data(data_path), specification=specification)


def _control_columns(frame: pd.DataFrame) -> list[str]:
    return [
        str(c)
        for c in frame.columns
        if str(c).startswith(CONTROL_PREFIX)
        and frame[c].dropna().nunique() > 1
    ]


def _metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, labels=LABELS, average="macro", zero_division=0)),
        "qwk": float(cohen_kappa_score(y_true, y_pred, labels=LABELS, weights="quadratic")),
        "ordinal_mae": float(mean_absolute_error(y_true, y_pred)),
    }


def _complete(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    return frame.loc[:, ["Y", *columns]].apply(pd.to_numeric, errors="coerce").dropna()


def _fit_ordered(train_x: pd.DataFrame, train_y: np.ndarray, test_x: pd.DataFrame) -> np.ndarray:
    model = OrderedModel(train_y.astype(int), train_x.astype(float), distr="logit")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = model.fit(method="bfgs", maxiter=800, disp=False)
    probabilities = np.asarray(result.model.predict(result.params, exog=test_x.astype(float)), dtype=float)
    return LABELS[np.argmax(probabilities, axis=1)]


def _fold_evaluation(frame: pd.DataFrame, feature_columns: list[str], model_name: str, *, folds: int = CV_FOLDS) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    work = _complete(frame, feature_columns)
    y = work["Y"].to_numpy(int)
    x = work[feature_columns].astype(float)
    splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=RANDOM_SEED)
    records: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    for fold, (train_idx, test_idx) in enumerate(splitter.split(x, y), start=1):
        x_train, x_test = x.iloc[train_idx], x.iloc[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        try:
            if model_name == "majority":
                values, counts = np.unique(y_train, return_counts=True)
                prediction = np.repeat(values[np.argmax(counts)], len(test_idx))
            elif model_name == "ordered_logit":
                prediction = _fit_ordered(x_train, y_train, x_test)
            elif model_name == "random_forest":
                estimator = RandomForestClassifier(n_estimators=200, max_depth=6, random_state=RANDOM_SEED, n_jobs=-1, class_weight=None)
                estimator.fit(x_train, y_train)
                prediction = estimator.predict(x_test).astype(int)
            else:
                raise ValueError(f"Unknown model: {model_name}")
            metric = _metrics(y_test, prediction)
            metric.update({"model": model_name, "feature_set": "|".join(feature_columns), "fold": fold, "n_test": len(test_idx), "status": "ok", "error": ""})
            records.append(metric)
            predictions.extend({"row_index": int(work.index[i]), "fold": fold, "model": model_name, "feature_set": "|".join(feature_columns), "y_true": int(y_test[j]), "y_pred": int(prediction[j])} for j, i in enumerate(test_idx))
        except Exception as exc:
            records.append({"model": model_name, "feature_set": "|".join(feature_columns), "fold": fold, "n_test": len(test_idx), "status": "failed", "error": f"{type(exc).__name__}: {exc}", "accuracy": np.nan, "macro_f1": np.nan, "qwk": np.nan, "ordinal_mae": np.nan})
    return pd.DataFrame(records), pd.DataFrame(predictions), {"n_obs": int(len(work)), "folds": folds}


def _aggregate_shap(raw: Any, n_features: int) -> np.ndarray:
    values = raw.values if hasattr(raw, "values") else raw
    if isinstance(values, list):
        values = np.stack(values, axis=-1)
    values = np.asarray(values, dtype=float)
    if values.ndim == 2:
        return values
    if values.ndim == 3:
        # samples x features x class; explain P(Y >= 4)
        return values[:, :, 3:].sum(axis=2)
    raise ValueError(f"Unexpected SHAP array shape: {values.shape}; expected two or three dimensions")


def _shap_oof(frame: pd.DataFrame, feature_columns: list[str], folds: int = CV_FOLDS) -> tuple[pd.DataFrame, dict[str, Any]]:
    try:
        import shap
    except ImportError as exc:
        return pd.DataFrame(), {"status": "unavailable", "error": str(exc)}
    work = _complete(frame, feature_columns)
    y = work["Y"].to_numpy(int)
    x = work[feature_columns].astype(float)
    splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=RANDOM_SEED)
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for fold, (train_idx, test_idx) in enumerate(splitter.split(x, y), start=1):
        try:
            estimator = RandomForestClassifier(n_estimators=200, max_depth=6, random_state=RANDOM_SEED, n_jobs=-1)
            estimator.fit(x.iloc[train_idx], y[train_idx])
            background = x.iloc[train_idx].sample(min(100, len(train_idx)), random_state=RANDOM_SEED)
            try:
                explainer = shap.TreeExplainer(estimator, data=background, feature_perturbation="interventional", model_output="probability")
                explained = explainer(x.iloc[test_idx])
                values = _aggregate_shap(explained, len(feature_columns))
            except Exception:
                # Older SHAP versions may not expose probability output for a
                # multiclass forest; retain a transparent fallback record.
                explainer = shap.TreeExplainer(estimator)
                explained = explainer(x.iloc[test_idx])
                values = _aggregate_shap(explained, len(feature_columns))
                errors.append(f"fold {fold}: probability output unavailable; used raw-output fallback")
            for local, original in enumerate(test_idx):
                for column_index, column in enumerate(feature_columns):
                    rows.append({"row_index": int(work.index[original]), "fold": fold, "feature": column, "shap_value": float(values[local, column_index])})
        except Exception as exc:
            errors.append(f"fold {fold}: {type(exc).__name__}: {exc}")
    if not rows:
        return pd.DataFrame(), {"status": "failed", "errors": errors}
    result = pd.DataFrame(rows)
    return result, {"status": "ok", "errors": errors, "target": "P(Y>=4) when supported; raw-output fallback is flagged"}


def run_ml_shap_analysis(
    df: pd.DataFrame | None = None,
    output_dir: str | Path = "figures/runs",
    *,
    data_path: str | Path = DATA_PATH,
    specification: str = "primary",
    folds: int = CV_FOLDS,
) -> dict[str, Any]:
    """Evaluate fixed feature sets and save out-of-fold metrics and SHAP."""

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    frame = df if df is not None and df.attrs.get("schema_specification") == specification else load_data(data_path, specification)
    controls = _control_columns(frame)
    feature_sets = {
        "controls": controls,
        "core": [*controls, "T", "V"],
        "extended": [*controls, "T", "V", "M1", "M2"],
    }
    model_rows: list[pd.DataFrame] = []
    prediction_rows: list[pd.DataFrame] = []
    run_meta: dict[str, Any] = {"specification": specification, "seed": RANDOM_SEED, "folds": folds, "feature_sets": {k: v for k, v in feature_sets.items()}}
    for feature_set, columns in feature_sets.items():
        for model in ("majority", "ordered_logit", "random_forest"):
            rows, predictions, meta = _fold_evaluation(frame, columns, model, folds=folds)
            rows["feature_set_name"] = feature_set
            predictions["feature_set_name"] = feature_set
            model_rows.append(rows)
            prediction_rows.append(predictions)
    fold_table = pd.concat(model_rows, ignore_index=True)
    prediction_table = pd.concat(prediction_rows, ignore_index=True)
    fold_table.to_csv(out / "ml_fold_metrics.csv", index=False)
    prediction_table.to_csv(out / "ml_oof_predictions.csv", index=False)
    summary = fold_table[fold_table["status"] == "ok"].groupby(["feature_set_name", "model"], as_index=False)[["accuracy", "macro_f1", "qwk", "ordinal_mae"]].agg(["mean", "std"]).reset_index()
    summary.columns = ["_".join(c).strip("_") if isinstance(c, tuple) else c for c in summary.columns]
    summary.to_csv(out / "ml_summary.csv", index=False)
    confusion_rows = []
    for keys, group in prediction_table.groupby(["feature_set_name", "model"]):
        matrix = confusion_matrix(group["y_true"], group["y_pred"], labels=LABELS)
        confusion_rows.append({"feature_set_name": keys[0], "model": keys[1], "matrix": matrix.tolist()})
    (out / "ml_confusion_matrices.json").write_text(json.dumps(confusion_rows, ensure_ascii=False, indent=2), encoding="utf-8")

    shap_table, shap_meta = _shap_oof(frame, feature_sets["extended"], folds=folds)
    if not shap_table.empty:
        shap_table.to_csv(out / "shap_oof_values.csv", index=False)
        importance = shap_table.assign(abs_shap=shap_table["shap_value"].abs()).groupby("feature", as_index=False)["abs_shap"].mean().rename(columns={"abs_shap": "mean_abs_shap"}).sort_values("mean_abs_shap", ascending=False)
        importance.to_csv(out / "shap_importance.csv", index=False)
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.barh(importance["feature"].iloc[::-1], importance["mean_abs_shap"].iloc[::-1], color="#377eb8")
        ax.set_xlabel("Mean absolute SHAP value")
        ax.set_title("Out-of-fold feature attribution for the extended forest")
        fig.tight_layout()
        fig.savefig(out / "shap_importance.png", dpi=160, facecolor="white")
        plt.close(fig)
    run_meta["shap"] = shap_meta
    (out / "ml_run_metadata.json").write_text(json.dumps(run_meta, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return {"fold_metrics": fold_table, "summary": summary, "predictions": prediction_table, "shap": shap_table, "metadata": run_meta}


if __name__ == "__main__":
    run_ml_shap_analysis()
