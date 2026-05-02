"""
REST API views for the grader service.

POST /api/grade/assessment/{assessment_id}/  — batch grade all attempts
POST /api/grade/attempt/{attempt_id}/        — grade a single attempt
"""

import logging

from django.http import Http404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from grader.serializers import BatchGradingResultSerializer, SingleGradingResultSerializer
from grader.services import GraderService

logger = logging.getLogger(__name__)


class AssessmentGradeView(APIView):
    """
    POST /api/grade/assessment/{assessment_id}/

    Grades all eligible (SUBMITTED or TIMED_OUT) attempts for the given assessment.
    Returns a summary with graded_count, grading_status, and plagiarism_flags.
    """

    def post(self, request: Request, assessment_id: int) -> Response:
        service = GraderService()
        try:
            result = service.grade_assessment(assessment_id)
        except Http404 as exc:
            return Response({"detail": str(exc)}, status=404)
        except Exception as exc:
            logger.exception("Unexpected error grading assessment %d", assessment_id)
            return Response({"detail": "Internal server error."}, status=500)

        serializer = BatchGradingResultSerializer(result)
        return Response(serializer.data, status=200)


class AttemptGradeView(APIView):
    """
    POST /api/grade/attempt/{attempt_id}/

    Grades a single attempt and returns per-answer feedback.
    """

    def post(self, request: Request, attempt_id: int) -> Response:
        service = GraderService()
        try:
            result = service.grade_attempt(attempt_id)
        except Http404 as exc:
            return Response({"detail": str(exc)}, status=404)
        except Exception as exc:
            logger.exception("Unexpected error grading attempt %d", attempt_id)
            return Response({"detail": "Internal server error."}, status=500)

        serializer = SingleGradingResultSerializer(result)
        return Response(serializer.data, status=200)
