"""
Grading scale utility.

Reads the GRADING_SCALE environment variable (JSON) at import time.
Default scale: {"A": 70, "B": 60, "C": 50, "D": 40}

The scale maps letter grades to minimum percentage thresholds (inclusive).
Grades are evaluated from highest threshold to lowest; anything below the
lowest threshold receives "F".
"""

import json
import os
from django.core.exceptions import ImproperlyConfigured


_DEFAULT_SCALE = {"A": 70, "B": 60, "C": 50, "D": 40}


def _load_scale() -> dict[str, int]:
    raw = os.environ.get("GRADING_SCALE")
    if raw is None:
        return _DEFAULT_SCALE
    try:
        scale = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ImproperlyConfigured(
            f"GRADING_SCALE is not valid JSON: {exc}"
        ) from exc
    if not isinstance(scale, dict):
        raise ImproperlyConfigured("GRADING_SCALE must be a JSON object.")
    return scale


class GradingScale:
    """
    Computes letter grades from a numeric score and total marks.

    The scale is loaded once at class definition time from the GRADING_SCALE
    environment variable (or the default scale if absent).
    """

    _scale: dict[str, int] = _load_scale()

    @classmethod
    def compute_grade(cls, score: float, total_marks: int) -> str:
        """
        Return the letter grade for a given score out of total_marks.

        The percentage is computed as (score / total_marks) * 100.
        Grades are evaluated from highest threshold to lowest.
        Returns "F" if the percentage is below all thresholds.

        Args:
            score: The numeric score achieved (0 <= score <= total_marks).
            total_marks: The maximum possible score (must be > 0).

        Returns:
            A letter grade string (e.g. "A", "B", "F").
        """
        if total_marks <= 0:
            return "F"

        percentage = (score / total_marks) * 100

        # Sort thresholds from highest to lowest so we assign the best
        # matching grade first.
        sorted_grades = sorted(
            cls._scale.items(), key=lambda item: item[1], reverse=True
        )

        for letter, threshold in sorted_grades:
            if percentage >= threshold:
                return letter

        return "F"


# Module-level convenience function (used in property-based tests)
def compute_grade(score: float, total_marks: int, scale: dict[str, int] | None = None) -> str:
    """
    Standalone compute_grade function for use in tests and utilities.

    If scale is provided, uses that scale instead of the class-level default.
    """
    if scale is None:
        return GradingScale.compute_grade(score, total_marks)

    if total_marks <= 0:
        return "F"

    percentage = (score / total_marks) * 100
    sorted_grades = sorted(scale.items(), key=lambda item: item[1], reverse=True)

    for letter, threshold in sorted_grades:
        if percentage >= threshold:
            return letter

    return "F"
