"""Command-line entry point for the reproducible EV purchase-intention project.

Examples::

    python main.py --analysis audit
    python main.py --analysis econometrics
    python main.py --analysis all

Each run is written to a new directory under ``figures/runs``. The source
survey is never overwritten and the raw CSV's historical processing columns
are never passed to a model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.config import DEFAULT_DATA_PATH, DEFAULT_OUTPUT_DIR, RANDOM_SEED
from src.data_schema import audit_data_path, load_raw_data, mapping_manifest


PROJECT_ROOT = Path(__file__).resolve().parent


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_state() -> dict[str, str | bool]:
    state: dict[str, str | bool] = {"commit": "unknown", "dirty": False}
    try:
        state["commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, text=True, stderr=subprocess.DEVNULL).strip()
        state["dirty"] = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=PROJECT_ROOT, text=True, stderr=subprocess.DEVNULL).strip())
    except Exception:
        pass
    return state


def _run_metadata(data_path: Path, analysis: str, args: argparse.Namespace) -> dict:
    return {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "analysis": analysis,
        "data_path": str(data_path),
        "data_sha256": _sha256(data_path),
        "random_seed": RANDOM_SEED,
        "bootstrap_iterations": args.bootstrap_iterations,
        "python": sys.version,
        "platform": platform.platform(),
        "git": _git_state(),
        "mapping": mapping_manifest(),
    }


def _save_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def run(args: argparse.Namespace) -> Path:
    data_path = Path(args.data).expanduser().resolve()
    output_root = Path(args.output_dir).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    run_name = datetime.now().strftime("run-%Y%m%d-%H%M%S")
    output_dir = output_root / run_name
    output_dir.mkdir(parents=True, exist_ok=False)
    metadata = _run_metadata(data_path, args.analysis, args)
    _save_json(output_dir / "run_metadata.json", metadata)

    raw = load_raw_data(data_path)
    if args.analysis in {"audit", "all"}:
        _save_json(output_dir / "audit.json", audit_data_path(data_path))
        print(f"Audit saved: {output_dir / 'audit.json'}")

    if args.analysis in {"econometrics", "all"}:
        from src.ordered_logit import run_ordered_logit_analysis

        run_ordered_logit_analysis(output_dir=output_dir, data_path=data_path)
        print(f"Ordered-logit results saved: {output_dir}")

    if args.analysis in {"mediation", "all"}:
        from src.mediation import run_mediation_analysis

        run_mediation_analysis(output_dir=output_dir, data_path=data_path, iterations=args.bootstrap_iterations)
        print(f"Mediation results saved: {output_dir}")

    if args.analysis in {"heterogeneity", "all"}:
        from src.heterogeneity import analyze_heterogeneity, heterogeneity_results_table, load_data as load_heterogeneity_data

        heterogeneity = analyze_heterogeneity(load_heterogeneity_data(data_path))
        heterogeneity_results_table(heterogeneity).to_csv(output_dir / "heterogeneity_results.csv", index=False)
        _save_json(output_dir / "heterogeneity_results.json", heterogeneity)
        print(f"Heterogeneity results saved: {output_dir}")

    if args.analysis in {"ml", "all"}:
        from src.ml_shap import run_ml_shap_analysis

        run_ml_shap_analysis(output_dir=output_dir, data_path=data_path)
        print(f"ML and SHAP results saved: {output_dir}")

    print(f"Run complete: {output_dir}")
    return output_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", choices=["audit", "econometrics", "mediation", "heterogeneity", "ml", "all"], default="all")
    parser.add_argument("--data", default=str(DEFAULT_DATA_PATH))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--bootstrap-iterations", type=int, default=5000)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
