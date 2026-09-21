"""Build the public, aggregate-only payload used by the GitHub Pages report.

The payload intentionally excludes raw respondents, out-of-fold predictions, and
row-level SHAP values. A run directory must contain the complete ``--analysis all``
artifacts before it can be published.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "figures" / "runs"
OUT = ROOT / "app" / "static" / "data" / "report.json"
REQUIRED = {
    "run_metadata.json",
    "audit.json",
    "ordered_logit_coefficients.csv",
    "ordered_logit_diagnostics.json",
    "mediation_paths.csv",
    "heterogeneity_results.csv",
    "ml_summary.csv",
    "ml_run_metadata.json",
    "shap_importance.csv",
}
MAIN_QUESTIONS = (1, 2, 4, 6, 9, 12, 15, 16, 17, 18, 19, 21, 22, 23, 24, 25)
GROUP_LABELS = {
    "gender_gp": "性别",
    "age_gp": "年龄",
    "income_gp": "月收入",
    "exp_gp": "驾龄",
    "freq_gp": "驾驶频率",
}
MEDIATOR_LABELS = {"Driving pleasure": "驾驶乐趣", "Travel efficiency": "出行效率", "Function-value proxy": "功能价值"}
X_LABELS = {"Technology proxy": "技术认知", "Function-value proxy": "功能价值"}
MODEL_LABELS = {"majority": "多数类基线", "ordered_logit": "有序 Logit", "random_forest": "随机森林"}
FEATURE_LABELS = {"controls": "控制变量", "core": "控制变量 + T/V", "extended": "扩展变量 + M1/M2"}


def json_safe(value):
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
        return None
    return value


def choose_run(run_id: str | None) -> Path:
    if run_id:
        path = RUN_ROOT / run_id
        if not path.is_dir():
            raise FileNotFoundError(path)
        return path
    candidates = []
    for path in sorted(RUN_ROOT.glob("run-*")):
        names = {p.name for p in path.iterdir()}
        if REQUIRED <= names:
            candidates.append(path)
    if not candidates:
        raise FileNotFoundError("No complete analysis run found")
    return candidates[-1]


def build(run_dir: Path) -> dict:
    metadata = json.loads((run_dir / "run_metadata.json").read_text(encoding="utf-8"))
    audit = json.loads((run_dir / "audit.json").read_text(encoding="utf-8"))
    coefficients = pd.read_csv(run_dir / "ordered_logit_coefficients.csv")
    diagnostics = json.loads((run_dir / "ordered_logit_diagnostics.json").read_text(encoding="utf-8"))
    mediation = pd.read_csv(run_dir / "mediation_paths.csv")
    heterogeneity = pd.read_csv(run_dir / "heterogeneity_results.csv")
    ml = pd.read_csv(run_dir / "ml_summary.csv")
    ml_meta = json.loads((run_dir / "ml_run_metadata.json").read_text(encoding="utf-8"))
    shap = pd.read_csv(run_dir / "shap_importance.csv")

    main_missing = {str(q): int(audit.get("missing_by_question", {}).get(str(q), 0)) for q in MAIN_QUESTIONS}
    main_out_of_range = {str(q): int(audit.get("out_of_range_by_question", {}).get(str(q), 0)) for q in MAIN_QUESTIONS}
    composites = {}
    for name in ("Y", "T_primary", "T_sensitivity", "V_primary", "M1", "M2"):
        item = audit.get("composites", {}).get(name)
        if item:
            composites[name] = {
                "questions": item.get("questions"),
                "complete_rows": item.get("complete_rows"),
                "missing_rows": item.get("missing_rows"),
                "mean": item.get("mean"),
                "std": item.get("std"),
                "cronbach_alpha": item.get("cronbach_alpha"),
            }

    direct = []
    for spec in ("primary", "sensitivity", "legacy"):
        rows = coefficients[
            (coefficients["specification"] == spec)
            & (coefficients["model"] == "controlled")
            & (coefficients["term_type"] == "predictor")
            & (coefficients["term"].isin(["T", "V"]))
        ]
        for _, row in rows.iterrows():
            direct.append({
                "specification": spec,
                "term": row["term"],
                "label": "技术认知 T" if row["term"] == "T" else "功能价值 V",
                "coefficient": row["coefficient"],
                "odds_ratio": row["odds_ratio"],
                "ci_low": float(np.exp(row["ci_low"])),
                "ci_high": float(np.exp(row["ci_high"])),
                "p_value": row["p_value"],
                "n_obs": row["n_obs"],
                "converged": diagnostics.get(spec, {}).get("controlled", {}).get("converged", False),
            })

    mediation_rows = []
    for _, row in mediation.iterrows():
        mediation_rows.append({
            "x": X_LABELS.get(row["x"], row["x"]),
            "mediator": MEDIATOR_LABELS.get(row["mediator"], row["mediator"]),
            "indirect": row["indirect"],
            "ci_low": row["ci_low"],
            "ci_high": row["ci_high"],
            "n_obs": row["n_obs"],
            "bootstrap_iterations": row["bootstrap_iterations"],
            "bootstrap_valid": row["bootstrap_valid"],
            "bootstrap_failures": row["bootstrap_failures"],
        })

    hetero_rows = []
    for _, row in heterogeneity.iterrows():
        hetero_rows.append({
            "group_var": row["group_var"],
            "label": GROUP_LABELS.get(row["group_var"], row["group_var"]),
            "n_obs": row["n_obs"],
            "n_groups": row["n_groups"],
            "lr_stat": row["lr_stat"],
            "df_diff": row["df_diff"],
            "p_raw": row["p_raw"],
            "p_holm": row["p_holm"],
            "status": row["status"],
        })

    ml_rows = []
    for _, row in ml.iterrows():
        ml_rows.append({
            "feature_set": row["feature_set_name"],
            "feature_label": FEATURE_LABELS.get(row["feature_set_name"], row["feature_set_name"]),
            "model": row["model"],
            "model_label": MODEL_LABELS.get(row["model"], row["model"]),
            "accuracy": row["accuracy_mean"],
            "accuracy_std": row["accuracy_std"],
            "macro_f1": row["macro_f1_mean"],
            "qwk": row["qwk_mean"],
            "qwk_std": row["qwk_std"],
            "mae": row["ordinal_mae_mean"],
        })

    top_shap = []
    for _, row in shap.sort_values("mean_abs_shap", ascending=False).head(6).iterrows():
        label = {
            "T": "技术认知 T",
            "V": "功能价值 V",
            "M1": "驾驶乐趣 M1",
            "M2": "出行效率 M2",
        }.get(row["feature"], row["feature"])
        top_shap.append({"feature": row["feature"], "label": label, "importance": row["mean_abs_shap"]})

    primary = [x for x in direct if x["specification"] == "primary"]
    extended_logit = next(x for x in ml_rows if x["feature_set"] == "extended" and x["model"] == "ordered_logit")
    extended_rf = next(x for x in ml_rows if x["feature_set"] == "extended" and x["model"] == "random_forest")
    return json_safe({
        "meta": {
            "run_id": run_dir.name,
            "created_at_utc": metadata.get("created_at_utc"),
            "data_sha256": metadata.get("data_sha256"),
            "random_seed": metadata.get("random_seed"),
            "bootstrap_iterations": metadata.get("bootstrap_iterations"),
            "git_commit": metadata.get("git", {}).get("commit"),
            "git_dirty": metadata.get("git", {}).get("dirty"),
        },
        "hero": {
            "n": audit.get("n_rows"),
            "primary_t_or": primary[0]["odds_ratio"],
            "primary_v_or": primary[1]["odds_ratio"],
            "extended_qwk": extended_logit["qwk"],
            "paths": len(mediation_rows),
        },
        "audit": {
            "n_rows": audit.get("n_rows"),
            "n_columns": audit.get("n_columns"),
            "duplicate_rows": audit.get("duplicate_rows"),
            "historical_processing_columns": audit.get("historical_processing_columns"),
            "main_missing": main_missing,
            "main_out_of_range": main_out_of_range,
            "q3_missing": audit.get("missing_by_question", {}).get("3", 0),
            "q3_out_of_range": audit.get("out_of_range_by_question", {}).get("3", 0),
            "composites": composites,
        },
        "direct": direct,
        "diagnostics": {
            spec: {
                "converged": values.get("controlled", {}).get("converged"),
                "aic": values.get("controlled", {}).get("aic"),
                "bic": values.get("controlled", {}).get("bic"),
                "prsquared": values.get("controlled", {}).get("prsquared"),
            }
            for spec, values in diagnostics.items()
        },
        "mediation": mediation_rows,
        "heterogeneity": hetero_rows,
        "ml": ml_rows,
        "ml_meta": {"folds": ml_meta.get("folds"), "shap": ml_meta.get("shap", {})},
        "shap": top_shap,
        "limits": {
            "association": "有序 Logit 结果是横截面条件关联，不是因果效果。",
            "mediation": "Bootstrap 路径是探索性间接关联，不能解释为因果中介。",
            "heterogeneity": "五组比较经过 Holm 校正后，没有形成稳定的显著异质性证据。",
            "ml": "机器学习用于折外预测和特征归因；SHAP 不是因果重要性。",
            "q3": "Q3 区域题是 8 类分类变量，通用 1–5 审计会标记 6–8；Q3 不进入当前主模型。",
        },
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", help="Complete run directory name, e.g. run-20260921-190434")
    parser.add_argument("--output", default=str(OUT))
    args = parser.parse_args()
    run_dir = choose_run(args.run_dir)
    payload = build(run_dir)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote aggregate report: {output}")
    print(f"Source run: {run_dir}")


if __name__ == "__main__":
    main()
