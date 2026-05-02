"""
Plagiarism detection via answer hash collision.

Scans student answers for identical answer hashes on the same question,
flagging all matching attempts as potential plagiarism cases.

This is a pure data-processing module with no database access.
"""

from collections import defaultdict


class PlagiarismScanner:
    """
    Detects plagiarism by finding answer hash collisions.

    Two or more answers for the same question with the same non-null
    answer_hash are considered a collision. All attempt IDs involved
    in a collision are flagged.

    # Feature: verion-ai-grader, Property 3: Plagiarism flags are symmetric
    """

    def build_collision_map(
        self,
        answers: list,
    ) -> dict[tuple[int, str], list[int]]:
        """
        Build a map of (question_id, answer_hash) -> [attempt_id, ...].

        Only entries with 2 or more attempt IDs represent actual collisions.
        Answers with null/empty answer_hash are excluded.

        Args:
            answers: Iterable of StudentAnswer-like objects with attributes:
                     question_id (int), answer_hash (str | None), attempt_id (int).

        Returns:
            A dict mapping (question_id, answer_hash) to a list of attempt_ids.
            Only keys with len(attempt_ids) > 1 indicate plagiarism.
        """
        groups: dict[tuple[int, str], list[int]] = defaultdict(list)

        for answer in answers:
            if not answer.answer_hash:
                continue
            key = (answer.question_id, answer.answer_hash)
            groups[key].append(answer.attempt_id)

        # Return only collision groups (2+ attempts with same hash)
        return {
            key: attempt_ids
            for key, attempt_ids in groups.items()
            if len(attempt_ids) > 1
        }

    def get_flagged_attempts(
        self,
        collision_map: dict[tuple[int, str], list[int]],
    ) -> set[int]:
        """
        Return the set of all attempt IDs that appear in any collision group.

        All attempts in a collision group are flagged — not just a subset.
        This ensures the plagiarism flag is symmetric.

        Args:
            collision_map: Output of build_collision_map().

        Returns:
            A set of attempt_ids that should be marked as plagiarism-flagged.

        # Feature: verion-ai-grader, Property 3: Plagiarism flags are symmetric
        """
        flagged: set[int] = set()
        for attempt_ids in collision_map.values():
            flagged.update(attempt_ids)
        return flagged
