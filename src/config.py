"""Shared, explicit configuration for the EV purchase-intention analyses.

The original project kept a copy of the questionnaire mapping in every analysis
module.  That made it easy for a notebook and a script to silently use different
questions.  This module is intentionally declarative: it contains the question
numbers, the fixed variable specifications, and run-level settings.  No value in
this file is selected from a p-value or a model score.
"""

from pathlib import Path


# Paths are resolved relative to the repository, so callers can run the modules
# from the project root or from another working directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "data.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "figures" / "runs"

RANDOM_SEED = 42
BOOTSTRAP_ITERATIONS = 5_000
CV_FOLDS = 5


# Exact raw questionnaire headers in data/raw/data.csv.  Keeping this mapping
# explicit prevents accidental use of the historical dummy-variable columns.
# The keys are questionnaire numbers used throughout the code and report.
QUESTION_TEXT = {
    1: "您的性别是?",
    2: "您的年龄是?",
    3: "您所在的区域是?",
    4: "您的最高学历是?",
    5: "您的职业是?",
    6: "您的月收入范围是?",
    7: "您的家庭常住人口数是?",
    8: "您未来购买汽车的意向是?",
    9: "您的驾龄是?",
    10: "您驾驶的主要目的是?",
    11: "您每天的日常通勤距离大约是?",
    12: "您每周驾驶的频率是?",
    13: "您通常的驾驶时间段是?",
    14: "您通常驾驶的车辆类型是?",
    15: "您认为智能驾驶功能对新能源汽车很重要?",
    16: "您认为智能驾驶功能可以提高驾驶安全性?",
    17: "您认为智能驾驶功能可以减轻驾驶疲劳?",
    18: "您认为智能驾驶功能可以提升驾驶乐趣?",
    19: "您认为智能驾驶功能可以提高出行效率?",
    20: "智能驾驶功能会影响您购买新能源汽车的决策?",
    21: "您愿意为智能驾驶功能支付溢价?",
    22: "您愿意为智能驾驶的自适应巡航功能影响购买意愿?",
    23: "您愿意为智能驾驶的车道保持辅助功能影响购买意愿?",
    24: "您愿意为智能驾驶的自动泊车功能影响购买意愿?",
    25: "您愿意为智能驾驶的交通拥堵辅助功能影响购买意愿?",
    26: "您愿意为智能驾驶未来技术更加成熟影响购买意愿?",
    27: "您愿意为智能驾驶未来安全性更高影响购买意愿?",
    28: "您愿意为智能驾驶未来成本更低影响购买意愿?",
    29: "您愿意为智能驾驶未来应用场景更丰富影响购买意愿?",
}

QUESTION_COLUMNS = {number: f"{number}.{text}" for number, text in QUESTION_TEXT.items()}


# Six controls are fixed for the main specifications.  Codes are kept as
# questionnaire category codes and are encoded as dummies by data_schema.py;
# they are deliberately not translated into unverified age, income, or year
# amounts.
CONTROL_QUESTION_NUMBERS = {
    "gender": 1,
    "age": 2,
    "education": 4,
    "income": 6,
    "driving_exp": 9,
    "driving_freq": 12,
}
CONTROL_LEVELS = {
    "gender": (1, 2),
    "age": (1, 2, 3, 4, 5),
    "education": (1, 2, 3, 4),
    "income": (1, 2, 3, 4, 5),
    "driving_exp": (1, 2, 3, 4, 5),
    "driving_freq": (1, 2, 3, 4, 5),
}


# Fixed analysis specifications.  ``legacy`` is retained solely for tracing
# the original project.  ``primary`` is the current specification; ``sensitivity``
# adds Q17 to the T proxy.  These definitions are fixed before fitting and are
# never chosen by significance.
MODEL_SPECS = {
    "legacy": {
        "technology_questions": (15, 16),
        "value_questions": (22,),
        "controls_encoding": "ordinal",
        "description": "Original two-item T and single-item V for traceability.",
    },
    "primary": {
        "technology_questions": (15, 16),
        "value_questions": (22, 23, 24, 25),
        "controls_encoding": "categorical",
        "description": "Two-item technology proxy and four-item function-value proxy.",
    },
    "sensitivity": {
        "technology_questions": (15, 16, 17),
        "value_questions": (22, 23, 24, 25),
        "controls_encoding": "categorical",
        "description": "Primary specification plus Q17 fatigue-relief recognition.",
    },
}


# Item-level composites use complete-case aggregation.  An unanswered item is
# not silently replaced by a scale mean; the row is marked missing for that
# composite and can be dropped by the analysis module.
COMPOSITE_MISSING_POLICY = "complete_case"
VALID_RESPONSE_RANGE = (1, 5)

# Deliberately excluded from the main feature set because they change the
# research question or overlap with the outcome: Q8, Q20, and Q26--Q29.
EXCLUDED_FROM_MAIN_FEATURES = (8, 20, 26, 27, 28, 29)


def question_column(number: int) -> str:
    """Return the expected raw CSV header for questionnaire ``number``."""

    try:
        return QUESTION_COLUMNS[int(number)]
    except (KeyError, TypeError, ValueError) as exc:
        raise KeyError(f"Unknown questionnaire number: {number!r}") from exc

