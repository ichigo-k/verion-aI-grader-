"""
Score computation utilities.

Provides functions for capping criterion scores and computing final attempt scores.
These are pure functions with no side effects, making them easy to test with
property-based testing.
"""


def cap_criterion_score(awarded: int, max_marks: int) -> int:
    """
    Cap a criterion score at its maximum allowed value.

    Ensures the awarded score is:
    - Not negative (clamped to 0)
    - Not greater than max_marks (clamped to max_marks)

    Args:
        awarded: The score awarded by the AI model for this criterion.
        max_marks: The maximum marks allowed for this criterion.

    Returns:
        The capped score: max(0, min(awarded, max_marks))

    # Feature: verion-ai-grader, Property 6: Per-criterion scores are individually capped
    """
    return max(0, min(awarded, max_marks))


def compute_final_score(
    mcq_score: float,
    subjective_scores: list[float],
    total_marks: int,
) -> float:
    """
    Compute the final score for an attempt.

    Sums the MCQ score and all subjective answer scores, then caps the result
    at total_marks. The result is also clamped to a minimum of 0.

    Args:
        mcq_score: The existing MCQ score already stored on the attempt (>= 0).
        subjective_scores: List of per-answer subjective scores (each >= 0).
        total_marks: The maximum possible score for the assessment (> 0).

    Returns:
        The final score: max(0, min(mcq_score + sum(subjective_scores), total_marks))

    # Feature: verion-ai-grader, Property 1: Score is bounded by assessment total marks
    """
    raw_total = mcq_score + sum(subjective_scores)
    return max(0.0, min(raw_total, float(total_marks)))
