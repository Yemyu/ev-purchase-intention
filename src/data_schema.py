"""Questionnaire mapping and feature construction for the EV survey.

The CSV in ``data/raw`` contains both the original questionnaire columns and
historical dummy/exception-handling columns.  Analysis modules should call this
module instead of selecting columns by position or by a partial string match.
All mappings are fixed in :mod:`src.config`; this module only applies those
definitions and records what happened to the data.

The public functions intentionally do not inspect p-values or model scores.  A
specification is selected explicitly (``legacy``, ``primary`` or
``sensitivity``), and missing observations are left as missing until an
analysis module applies its declared complete-case rule.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

from .config import (
    COMPOSITE_MISSING_POLICY,
    CONTROL_LEVELS,
    CONTROL_QUESTION_NUMBERS,
    MODEL_SPECS,
    QUESTION_COLUMNS,
    QUESTION_TEXT,
    VALID_RESPONSE_RANGE,
)


class SchemaError(ValueError):
    """Raised when a dataset cannot satisfy an explicit schema requirement."""


@dataclass(frozen=True)
class CompositeSpec:
    """Description of one derived survey measure.

    ``questions`` contains questionnaire numbers rather than CSV positions.
    ``policy`` documents how an item-level missing value is treated.  The
    current project uses complete-case item aggregation for every composite.
    """

    name: str
    questions: tuple[int, ...]
    label: str
    policy: str = COMPOSITE_MISSING_POLICY


COMPOSITES: Mapping[str, CompositeSpec] = {
    "Y": CompositeSpec("Y", (21,), "willingness to pay a premium"),
    "T_legacy": CompositeSpec("T_legacy", (15, 16), "legacy technology proxy"),
    "T_primary": CompositeSpec("T_primary", (15, 16), "technology importance and safety proxy"),
    "T_sensitivity": CompositeSpec(
        "T_sensitivity", (15, 16, 17), "technology proxy including fatigue relief"
    ),
    "V_legacy": CompositeSpec("V_legacy", (22,), "legacy function-value proxy"),
    "V_primary": CompositeSpec(
        "V_primary", (22, 23, 24, 25), "four assisted-driving function-value proxy"
    ),
    "M1": CompositeSpec("M1", (18,), "driving pleasure recognition"),
    "M2": CompositeSpec("M2", (19,), "travel efficiency recognition"),
}

# Short aliases used in tables and by downstream modules.  ``T`` and ``V`` are
# assigned to the explicitly requested specification in build_analysis_frame.
PRIMARY_OUTPUT_COLUMNS = ("Y", "T", "V", "M1", "M2")


def _question_number_from_header(header: str) -> int | None:
    """Extract a leading questionnaire number from a CSV header."""

    match = re.match(r"^\s*(\d+)\.", str(header))
    return int(match.group(1)) if match else None


def resolve_question_columns(
    frame: pd.DataFrame,
    required: Iterable[int] | None = None,
) -> dict[int, str]:
    """Resolve questionnaire numbers to raw columns in ``frame``.

    Exact headers from :mod:`src.config` are preferred.  A fallback accepts a
    header with harmless surrounding whitespace, while still rejecting the
    historical columns whose names contain suffixes such as ``_哑变量化`` or
    ``_异常值处理``.  A :class:`SchemaError` lists every missing number.
    """

    numbers = tuple(sorted(set(int(n) for n in (required or QUESTION_COLUMNS))))
    columns = [str(c).lstrip("\ufeff") for c in frame.columns]
    # Preserve the original pandas labels if they contain non-string objects.
    by_text = {str(c).lstrip("\ufeff"): c for c in frame.columns}
    resolved: dict[int, str] = {}
    for number in numbers:
        expected = QUESTION_COLUMNS.get(number)
        if expected is None:
            raise SchemaError(f"Unknown questionnaire number: {number}")
        if expected in by_text:
            resolved[number] = by_text[expected]
            continue

        # Only an unsuffixed header is a raw item.  This avoids accidentally
        # resolving e.g. Q15 to a historical one-hot column.
        candidates = [
            original
            for original, text in zip(frame.columns, columns)
            if _question_number_from_header(text) == number
            and text.strip() == expected
        ]
        if candidates:
            resolved[number] = candidates[0]

    missing = [number for number in numbers if number not in resolved]
    if missing:
        details = ", ".join(f"Q{number} ({QUESTION_TEXT[number]})" for number in missing)
        raise SchemaError(f"Missing required questionnaire columns: {details}")
    return resolved


def load_raw_data(data_path: str | Path) -> pd.DataFrame:
    """Read a survey CSV with UTF-8/BOM handling and return a fresh frame."""

    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Survey data not found: {path}")
    # utf-8-sig accepts both ordinary UTF-8 and the BOM present in some Excel
    # exports.  Do not drop or rename any source columns here.
    return pd.read_csv(path, encoding="utf-8-sig")


def _numeric_item(frame: pd.DataFrame, column: str) -> pd.Series:
    """Convert one item to numeric while preserving invalid entries as NA."""

    return pd.to_numeric(frame[column], errors="coerce")


def _aggregate_items(frame: pd.DataFrame, question_columns: Mapping[int, str], questions: Sequence[int]) -> pd.Series:
    """Aggregate Likert items under the configured complete-case policy."""

    items = pd.concat(
        [_numeric_item(frame, question_columns[number]).rename(f"Q{number}") for number in questions],
        axis=1,
    )
    if COMPOSITE_MISSING_POLICY == "complete_case":
        return items.mean(axis=1, skipna=False)
    raise SchemaError(f"Unsupported composite missing policy: {COMPOSITE_MISSING_POLICY!r}")


def _required_questions_for_spec(specification: str) -> tuple[int, ...]:
    """Return the exact raw question numbers required by a model specification."""

    if specification not in MODEL_SPECS:
        raise SchemaError(
            f"Unknown specification {specification!r}; choose one of {sorted(MODEL_SPECS)}"
        )
    model = MODEL_SPECS[specification]
    required = {
        21,
        *model["technology_questions"],
        *model["value_questions"],
        18,
        19,
        *CONTROL_QUESTION_NUMBERS.values(),
    }
    return tuple(sorted(required))


def _raw_question_frame(
    frame: pd.DataFrame,
    question_columns: Mapping[int, str],
    numbers: Iterable[int],
) -> pd.DataFrame:
    """Create stable ``Q<number>`` columns without touching source columns."""

    return pd.DataFrame(
        {f"Q{number}": _numeric_item(frame, question_columns[number]) for number in numbers},
        index=frame.index,
    )


def encode_controls(
    frame: pd.DataFrame,
    *,
    controls: Sequence[str] | None = None,
    drop_first: bool = True,
    keep_non_controls: bool = True,
) -> pd.DataFrame:
    """Encode fixed background controls as deterministic category dummies.

    The source values are questionnaire category codes.  The first configured
    level is the reference (for example, code ``1`` for gender).  Missing
    controls remain missing in every dummy column; they are not converted to
    the reference category.  This function does not infer numeric age, income,
    or driving-experience amounts.

    Parameters
    ----------
    frame:
        Frame containing columns named by ``CONTROL_QUESTION_NUMBERS``.
    controls:
        Controls to encode; defaults to all six fixed controls.
    drop_first:
        Drop each control's configured reference level to avoid a dummy trap.
    keep_non_controls:
        Keep all columns other than raw control columns in the returned frame.
    """

    controls = tuple(controls or CONTROL_QUESTION_NUMBERS)
    unknown = [name for name in controls if name not in CONTROL_QUESTION_NUMBERS]
    if unknown:
        raise SchemaError(f"Unknown controls: {unknown}")
    missing = [name for name in controls if name not in frame.columns]
    if missing:
        raise SchemaError(f"Control columns not present in frame: {missing}")

    parts: list[pd.DataFrame] = []
    if keep_non_controls:
        parts.append(frame.drop(columns=list(controls)).copy())

    for name in controls:
        levels = tuple(CONTROL_LEVELS[name])
        values = pd.to_numeric(frame[name], errors="coerce")
        unexpected = values.notna() & ~values.isin(levels)
        if unexpected.any():
            observed = sorted({float(value) for value in values.loc[unexpected].unique()})
            raise SchemaError(
                f"Unexpected category code(s) for {name}: {observed}; "
                f"configured levels are {list(levels)}"
            )
        categorical = pd.Categorical(values, categories=levels, ordered=True)
        dummies = pd.get_dummies(categorical, prefix=f"control_{name}", dtype=float)
        if drop_first and dummies.shape[1]:
            dummies = dummies.iloc[:, 1:]
        # get_dummies represents NA as all zero.  Keep it explicitly missing so
        # a model can apply a declared row-complete rule later.
        dummies.loc[values.isna(), :] = np.nan
        dummies.index = frame.index
        parts.append(dummies)

    return pd.concat(parts, axis=1)


def add_derived_variables(
    frame: pd.DataFrame,
    *,
    specification: str = "primary",
    include_question_columns: bool = True,
    include_all_specifications: bool = True,
) -> pd.DataFrame:
    """Add Q columns and all fixed derived variables to a copy of ``frame``.

    ``specification`` determines which T/V aliases are exposed as ``T`` and
    ``V``.  Named legacy, primary and sensitivity composites are retained in
    every output by default so that sensitivity comparisons use the same raw
    rows and cannot silently change the item mapping.
    """

    required_set = set(_required_questions_for_spec(specification))
    if include_all_specifications:
        # The audit-friendly output keeps every named legacy/primary/sensitivity
        # composite, so resolve all of their source items before constructing it.
        for composite in COMPOSITES.values():
            required_set.update(composite.questions)
    required = tuple(sorted(required_set))
    question_columns = resolve_question_columns(frame, required=required)
    out = frame.copy()
    qframe = _raw_question_frame(frame, question_columns, required)
    if include_question_columns:
        for column in qframe.columns:
            out[column] = qframe[column]

    technology_name = "T_sensitivity" if specification == "sensitivity" else f"T_{specification}"
    value_name = "V_legacy" if specification == "legacy" else "V_primary"
    composite_names = tuple(COMPOSITES) if include_all_specifications else (
        "Y",
        technology_name,
        value_name,
        "M1",
        "M2",
    )
    for name in composite_names:
        composite = COMPOSITES[name]
        out[name] = _aggregate_items(frame, question_columns, composite.questions)

    model = MODEL_SPECS[specification]
    out["T"] = out[technology_name]
    out["V"] = out[value_name]
    # Compatibility aliases make the shared schema usable by the existing
    # modules while the descriptive T/V names remain the canonical columns.
    out["tech_trust"] = out["T"]
    out["perceived_value"] = out["V"]

    for name, question_number in CONTROL_QUESTION_NUMBERS.items():
        out[name] = _numeric_item(frame, question_columns[question_number])
    out.attrs["schema_specification"] = specification
    out.attrs["schema_question_columns"] = dict(question_columns)
    out.attrs["schema_model_spec"] = dict(model)
    return out


def build_analysis_frame(
    frame: pd.DataFrame,
    *,
    specification: str = "primary",
    encode_categories: bool | None = None,
    include_question_columns: bool = False,
) -> pd.DataFrame:
    """Return the compact feature frame used by an analysis module.

    The primary and sensitivity specifications encode controls categorically by
    default.  The legacy specification preserves ordinal control codes by
    default so its output remains traceable to the original project.  Pass
    ``encode_categories`` explicitly to override this behavior.  Rows with
    missing values are retained; each model decides whether its declared
    complete-case sample is appropriate.
    """

    derived = add_derived_variables(
        frame,
        specification=specification,
        include_question_columns=include_question_columns,
    )
    if encode_categories is None:
        encode_categories = MODEL_SPECS[specification]["controls_encoding"] == "categorical"
    # Select only schema-derived features and fixed controls.  In particular,
    # historical one-hot and exception-handling columns from the source CSV are
    # never passed through to an analysis model.
    canonical = [
        "Y",
        "T",
        "V",
        "T_legacy",
        "T_primary",
        "T_sensitivity",
        "V_legacy",
        "V_primary",
        "M1",
        "M2",
        "tech_trust",
        "perceived_value",
    ]
    control_columns = list(CONTROL_QUESTION_NUMBERS)
    question_columns = [column for column in derived.columns if re.fullmatch(r"Q\d+", str(column))]
    keep = canonical + control_columns + (question_columns if include_question_columns else [])
    out = derived.loc[:, [column for column in keep if column in derived.columns]].copy()
    if encode_categories:
        out = encode_controls(out, keep_non_controls=True)
    out.attrs.update(derived.attrs)
    out.attrs["encoded_controls"] = bool(encode_categories)
    return out


def cronbach_alpha(frame: pd.DataFrame, questions: Sequence[int]) -> float | None:
    """Compute a simple complete-row Cronbach alpha for item diagnostics.

    Alpha is reported as a descriptive check only; it is not used to choose a
    specification or to drop an item.  A one-item measure has no alpha.
    """

    if len(questions) < 2:
        return None
    columns = [f"Q{number}" if f"Q{number}" in frame else str(number) for number in questions]
    items = frame[columns].apply(pd.to_numeric, errors="coerce").dropna()
    if len(items) < 2:
        return None
    item_variances = items.var(axis=0, ddof=1).sum()
    total_variance = items.sum(axis=1).var(ddof=1)
    if total_variance <= 0 or not np.isfinite(total_variance):
        return None
    k = len(columns)
    return float(k / (k - 1) * (1 - item_variances / total_variance))


def audit_data(frame: pd.DataFrame) -> dict[str, Any]:
    """Return a JSON-friendly audit summary of raw columns and fixed features.

    The audit records row counts, duplicate rows, missingness, out-of-range
    Likert values, item summaries, control categories, historical processing
    columns, and fixed composite diagnostics.  It does not remove rows or
    make a significance-based selection.
    """

    try:
        question_columns = resolve_question_columns(frame)
        missing_questions: list[int] = []
    except SchemaError as exc:
        # Audit should still be useful for a partial/exported file.
        question_columns = {}
        for number, expected in QUESTION_COLUMNS.items():
            if expected in frame.columns:
                question_columns[number] = expected
        missing_questions = [number for number in QUESTION_COLUMNS if number not in question_columns]
        resolution_error = str(exc)

    summary: dict[str, Any] = {
        "n_rows": int(len(frame)),
        "n_columns": int(frame.shape[1]),
        "duplicate_rows": int(frame.duplicated().sum()),
        "resolved_question_columns": {str(number): str(column) for number, column in question_columns.items()},
        "missing_question_numbers": [int(number) for number in missing_questions],
        "historical_processing_columns": int(
            sum("_哑变量化" in str(column) or "_异常值处理" in str(column) for column in frame.columns)
        ),
        "missing_by_question": {},
        "out_of_range_by_question": {},
        "question_summary": {},
        "control_categories": {},
        "composites": {},
    }
    if "resolution_error" in locals():
        summary["resolution_error"] = resolution_error

    low, high = VALID_RESPONSE_RANGE
    for number, column in question_columns.items():
        values = pd.to_numeric(frame[column], errors="coerce")
        summary["missing_by_question"][str(number)] = int(values.isna().sum())
        out_of_range = values.notna() & ~values.between(low, high)
        summary["out_of_range_by_question"][str(number)] = int(out_of_range.sum())
        summary["question_summary"][str(number)] = {
            "column": str(column),
            "n": int(values.notna().sum()),
            "mean": float(values.mean()) if values.notna().any() else None,
            "std": float(values.std(ddof=1)) if values.notna().sum() > 1 else None,
            "unique_values": sorted(
                [int(v) if float(v).is_integer() else float(v) for v in values.dropna().unique()]
            ),
        }

    for name, question_number in CONTROL_QUESTION_NUMBERS.items():
        if question_number not in question_columns:
            continue
        values = pd.to_numeric(frame[question_columns[question_number]], errors="coerce")
        summary["control_categories"][name] = {
            "question": int(question_number),
            "counts": {
                str(int(value)): int(count)
                for value, count in values.value_counts(dropna=False).sort_index().items()
                if pd.notna(value)
            },
            "missing": int(values.isna().sum()),
        }

    # Compute composite checks only when their source items are available.
    if question_columns:
        for name, composite in COMPOSITES.items():
            if not all(number in question_columns for number in composite.questions):
                continue
            items = pd.concat(
                [_numeric_item(frame, question_columns[number]) for number in composite.questions], axis=1
            )
            complete = items.notna().all(axis=1)
            values = items.mean(axis=1, skipna=False)
            info: dict[str, Any] = {
                "questions": [int(number) for number in composite.questions],
                "label": composite.label,
                "complete_rows": int(complete.sum()),
                "missing_rows": int((~complete).sum()),
                "mean": float(values.mean()) if values.notna().any() else None,
                "std": float(values.std(ddof=1)) if values.notna().sum() > 1 else None,
            }
            if len(composite.questions) >= 2:
                qframe = items.copy()
                qframe.columns = [f"Q{number}" for number in composite.questions]
                info["cronbach_alpha"] = cronbach_alpha(qframe, composite.questions)
                info["pairwise_correlation"] = (
                    float(qframe.corr().iloc[0, 1])
                    if qframe.shape[1] == 2 and qframe.dropna().shape[0] >= 2
                    else None
                )
            summary["composites"][name] = info
    return summary


def audit_data_path(data_path: str | Path) -> dict[str, Any]:
    """Load a CSV and return :func:`audit_data` for convenience."""

    return audit_data(load_raw_data(data_path))


def mapping_manifest() -> dict[str, Any]:
    """Return the fixed mapping in a serializable form for run metadata."""

    return {
        "question_columns": {str(number): column for number, column in QUESTION_COLUMNS.items()},
        "controls": {
            name: {"question": int(question), "levels": list(CONTROL_LEVELS[name])}
            for name, question in CONTROL_QUESTION_NUMBERS.items()
        },
        "composites": {
            name: {"questions": list(spec.questions), "label": spec.label, "missing_policy": spec.policy}
            for name, spec in COMPOSITES.items()
        },
        "model_specs": {
            name: {
                "technology_questions": list(spec["technology_questions"]),
                "value_questions": list(spec["value_questions"]),
                "controls_encoding": spec["controls_encoding"],
            }
            for name, spec in MODEL_SPECS.items()
        },
    }
