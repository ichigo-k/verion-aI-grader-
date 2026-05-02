"""
AWS Bedrock client for AI-powered answer grading.

Wraps boto3's bedrock-runtime client to invoke a configured model with
structured prompts and parse the JSON response into GradeResponse objects.

Retry logic: one retry with exponential backoff (1s, then 2s) on throttling
or timeout errors. A second failure raises BedrockGradingError.

# Feature: verion-ai-grader, Property 4: Bedrock failure for one answer does not prevent others
"""

import json
import logging
import time
from dataclasses import dataclass, field

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Task 8.5 — Data types
# ---------------------------------------------------------------------------

@dataclass
class CriterionScore:
    """Score and justification for a single rubric criterion."""
    criterion: str
    awarded: int
    max: int
    justification: str


@dataclass
class GradeResponse:
    """
    Parsed response from the Bedrock model for a single answer.

    Attributes:
        criteria_scores: Per-criterion scores (empty list for holistic grading).
        holistic_score: Score for holistic grading (None for rubric grading).
        overall_feedback: Textual feedback for the answer.
        flag: One of "none", "suspicious", "incomplete", "off_topic".
        flag_reason: Explanation of the flag (empty string if flag is "none").
    """
    criteria_scores: list[CriterionScore] = field(default_factory=list)
    holistic_score: int | None = None
    overall_feedback: str = ""
    flag: str = "none"
    flag_reason: str = ""


class BedrockGradingError(Exception):
    """
    Raised when the Bedrock client fails to grade an answer.

    This includes:
    - boto3 ClientError after retries are exhausted
    - JSON parse failure on the model response
    - Missing required fields in the model response
    """
    pass


# ---------------------------------------------------------------------------
# Task 8.1 — BedrockClient class
# ---------------------------------------------------------------------------

class BedrockClient:
    """
    Wraps boto3 bedrock-runtime to grade student answers using a configured model.

    Usage:
        client = BedrockClient(
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            max_tokens=2048,
            region="us-east-1",
        )
        response = client.grade_answer(
            question_body="Explain photosynthesis.",
            answer_text="Photosynthesis is...",
            rubric_criteria=[{"description": "Accuracy", "max_marks": 5}],
            question_marks=5,
        )
    """

    # Retry configuration
    _MAX_RETRIES = 1
    _BACKOFF_SECONDS = [1, 2]
    _THROTTLING_ERRORS = {"ThrottlingException", "ServiceUnavailableException"}
    _TIMEOUT_ERRORS = {"RequestTimeoutException", "ReadTimeoutError"}

    def __init__(self, model_id: str, max_tokens: int, region: str) -> None:
        self._model_id = model_id
        self._max_tokens = max_tokens
        self._client = boto3.client("bedrock-runtime", region_name=region)

    # ---------------------------------------------------------------------------
    # Task 8.2 — Prompt construction
    # ---------------------------------------------------------------------------

    def _build_rubric_prompt(
        self,
        question_body: str,
        answer_text: str,
        rubric_criteria: list[dict],
    ) -> str:
        """Build a rubric-guided grading prompt."""
        rubric_lines = "\n".join(
            f"- {c['description']}: {c['max_marks']} marks"
            for c in rubric_criteria
        )
        return f"""You are an academic grader. Grade the following student answer using the provided rubric.

Question: {question_body}

Rubric:
{rubric_lines}

Student Answer:
{answer_text}

Return ONLY a JSON object with this exact structure:
{{
  "criteria_scores": [
    {{"criterion": "<description>", "awarded": <int>, "max": <int>, "justification": "<text>"}}
  ],
  "overall_feedback": "<text>",
  "flag": "<none|suspicious|incomplete|off_topic>",
  "flag_reason": "<text or empty>"
}}"""

    def _build_holistic_prompt(
        self,
        question_body: str,
        answer_text: str,
        question_marks: int,
    ) -> str:
        """Build a holistic grading prompt (no rubric)."""
        return f"""You are an academic grader. Grade the following student answer holistically.

Question: {question_body}

Student Answer:
{answer_text}

Score the answer holistically out of {question_marks} marks.
Return ONLY a JSON object:
{{
  "holistic_score": <int>,
  "overall_feedback": "<text>",
  "flag": "<none|suspicious|incomplete|off_topic>",
  "flag_reason": "<text or empty>"
}}"""

    # ---------------------------------------------------------------------------
    # Task 8.3 — JSON response parsing
    # ---------------------------------------------------------------------------

    def _parse_rubric_response(self, raw: str) -> GradeResponse:
        """Parse a rubric-guided model response into a GradeResponse."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise BedrockGradingError(
                f"Failed to parse Bedrock JSON response: {exc}. "
                f"Raw response (first 200 chars): {raw[:200]!r}"
            ) from exc

        required_fields = {"criteria_scores", "overall_feedback", "flag", "flag_reason"}
        missing = required_fields - data.keys()
        if missing:
            raise BedrockGradingError(
                f"Bedrock response missing required fields: {missing}. "
                f"Raw response (first 200 chars): {raw[:200]!r}"
            )

        criteria_scores = []
        for item in data["criteria_scores"]:
            criteria_scores.append(CriterionScore(
                criterion=item.get("criterion", ""),
                awarded=int(item.get("awarded", 0)),
                max=int(item.get("max", 0)),
                justification=item.get("justification", ""),
            ))

        return GradeResponse(
            criteria_scores=criteria_scores,
            holistic_score=None,
            overall_feedback=data.get("overall_feedback", ""),
            flag=data.get("flag", "none"),
            flag_reason=data.get("flag_reason", ""),
        )

    def _parse_holistic_response(self, raw: str) -> GradeResponse:
        """Parse a holistic model response into a GradeResponse."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise BedrockGradingError(
                f"Failed to parse Bedrock JSON response: {exc}. "
                f"Raw response (first 200 chars): {raw[:200]!r}"
            ) from exc

        required_fields = {"holistic_score", "overall_feedback", "flag", "flag_reason"}
        missing = required_fields - data.keys()
        if missing:
            raise BedrockGradingError(
                f"Bedrock response missing required fields: {missing}. "
                f"Raw response (first 200 chars): {raw[:200]!r}"
            )

        return GradeResponse(
            criteria_scores=[],
            holistic_score=int(data["holistic_score"]),
            overall_feedback=data.get("overall_feedback", ""),
            flag=data.get("flag", "none"),
            flag_reason=data.get("flag_reason", ""),
        )

    # ---------------------------------------------------------------------------
    # Task 8.4 — Retry logic
    # ---------------------------------------------------------------------------

    def _invoke_with_retry(self, prompt: str) -> str:
        """
        Invoke the Bedrock model with one retry on throttling/timeout.

        Returns the raw text content from the model response.
        Raises BedrockGradingError after retries are exhausted.
        """
        last_error: Exception | None = None

        for attempt in range(self._MAX_RETRIES + 1):
            try:
                response = self._client.invoke_model(
                    modelId=self._model_id,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps({
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": self._max_tokens,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                    }),
                )
                body = json.loads(response["body"].read())
                # Claude response format
                return body["content"][0]["text"]

            except ClientError as exc:
                error_code = exc.response["Error"]["Code"]
                is_retryable = (
                    error_code in self._THROTTLING_ERRORS
                    or error_code in self._TIMEOUT_ERRORS
                )
                last_error = exc

                if is_retryable and attempt < self._MAX_RETRIES:
                    wait = self._BACKOFF_SECONDS[attempt]
                    logger.warning(
                        "Bedrock %s on attempt %d/%d, retrying in %ds",
                        error_code, attempt + 1, self._MAX_RETRIES + 1, wait,
                    )
                    time.sleep(wait)
                    continue

                # Non-retryable error or retries exhausted
                raise BedrockGradingError(
                    f"Bedrock ClientError ({error_code}) after {attempt + 1} attempt(s): {exc}"
                ) from exc

            except Exception as exc:
                raise BedrockGradingError(
                    f"Unexpected error invoking Bedrock: {exc}"
                ) from exc

        # Should not reach here, but satisfy type checker
        raise BedrockGradingError(
            f"Bedrock invocation failed after retries: {last_error}"
        )

    # ---------------------------------------------------------------------------
    # Task 8.1 — Public interface
    # ---------------------------------------------------------------------------

    def grade_answer(
        self,
        question_body: str,
        answer_text: str,
        rubric_criteria: list[dict],
        question_marks: int,
    ) -> GradeResponse:
        """
        Grade a student answer using the configured Bedrock model.

        Uses a rubric-guided prompt when rubric_criteria is non-empty,
        otherwise uses a holistic prompt.

        Args:
            question_body: The question text.
            answer_text: The student's answer text.
            rubric_criteria: List of dicts with 'description' and 'max_marks'.
                             Pass an empty list for holistic grading.
            question_marks: Total marks for this question (used in holistic mode).

        Returns:
            GradeResponse with parsed scores and feedback.

        Raises:
            BedrockGradingError: If the model invocation or response parsing fails.
        """
        if rubric_criteria:
            prompt = self._build_rubric_prompt(question_body, answer_text, rubric_criteria)
            raw = self._invoke_with_retry(prompt)
            return self._parse_rubric_response(raw)
        else:
            prompt = self._build_holistic_prompt(question_body, answer_text, question_marks)
            raw = self._invoke_with_retry(prompt)
            return self._parse_holistic_response(raw)
