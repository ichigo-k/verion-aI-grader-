from django.db import models

# NOTE: All models in the first section of this file use managed=False.
# Running `python manage.py makemigrations` will NOT generate any migration
# for these models. Only GradingResult and AnswerFeedback (added in task 4)
# will appear in grader migrations.


# ---------------------------------------------------------------------------
# Read-only models — managed=False
# These map to tables owned by the main system (ai-powered-grading-system).
# Django will never run CREATE/ALTER/DROP against these tables.
# ---------------------------------------------------------------------------

class Assessment(models.Model):
    id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=255)
    total_marks = models.IntegerField(db_column='totalMarks')
    grading_status = models.CharField(max_length=20, db_column='gradingStatus')
    status = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'assessments'

    def __str__(self) -> str:
        return f"Assessment(id={self.id}, title={self.title!r})"


class AssessmentSection(models.Model):
    id = models.IntegerField(primary_key=True)
    assessment_id = models.IntegerField(db_column='assessmentId')
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20)  # 'SUBJECTIVE' | 'OBJECTIVE'

    class Meta:
        managed = False
        db_table = 'assessment_sections'

    def __str__(self) -> str:
        return f"AssessmentSection(id={self.id}, type={self.type!r})"


class AssessmentAttempt(models.Model):
    id = models.IntegerField(primary_key=True)
    assessment_id = models.IntegerField(db_column='assessmentId')
    student_id = models.IntegerField(db_column='studentId')
    status = models.CharField(max_length=20)
    score = models.FloatField(null=True, blank=True)
    # NOTE: grade column was dropped — grade letters are computed on read
    # by the main system from system_settings.gradingScale. Do not add it back.

    class Meta:
        managed = False
        db_table = 'assessment_attempts'

    def __str__(self) -> str:
        return f"AssessmentAttempt(id={self.id}, status={self.status!r})"


class Question(models.Model):
    id = models.IntegerField(primary_key=True)
    assessment_id = models.IntegerField(db_column='assessmentId')
    section_id = models.IntegerField(db_column='sectionId')
    body = models.TextField()
    marks = models.IntegerField()
    answer_type = models.CharField(max_length=20, null=True, blank=True, db_column='answerType')

    class Meta:
        managed = False
        db_table = 'questions'

    def __str__(self) -> str:
        return f"Question(id={self.id}, marks={self.marks})"


class RubricCriterion(models.Model):
    id = models.IntegerField(primary_key=True)
    question_id = models.IntegerField(db_column='questionId')
    description = models.TextField()
    max_marks = models.IntegerField(db_column='maxMarks')
    order = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'rubric_criteria'

    def __str__(self) -> str:
        return f"RubricCriterion(id={self.id}, max_marks={self.max_marks})"


class StudentAnswer(models.Model):
    id = models.IntegerField(primary_key=True)
    attempt_id = models.IntegerField(db_column='attemptId')
    question_id = models.IntegerField(db_column='questionId')
    answer_text = models.TextField(null=True, blank=True, db_column='answerText')
    file_url = models.TextField(null=True, blank=True, db_column='fileUrl')
    answer_hash = models.CharField(max_length=64, null=True, blank=True, db_column='answerHash')

    class Meta:
        managed = False
        db_table = 'student_answers'

    def __str__(self) -> str:
        return f"StudentAnswer(id={self.id}, question_id={self.question_id})"


# ---------------------------------------------------------------------------
# Grader-owned models — managed=False
# These tables are created and migrated by Prisma (ai-powered-grading-system).
# Django reads and writes them but NEVER runs CREATE/ALTER/DROP against them.
# ---------------------------------------------------------------------------

class GradingResult(models.Model):
    """One row per graded attempt. Stores the computed score and audit info."""
    attempt_id = models.IntegerField(unique=True, db_index=True, db_column='attemptId')
    assessment_id = models.IntegerField(db_index=True, db_column='assessmentId')
    score = models.FloatField()
    # grade is intentionally NOT stored — computed on read by the main system
    # from system_settings.gradingScale so it always reflects the current scale.
    plagiarism_flagged = models.BooleanField(default=False, db_column='plagiarismFlagged')
    graded_at = models.DateTimeField(db_column='gradedAt')
    error_notes = models.TextField(blank=True, default='', db_column='errorNotes')

    class Meta:
        managed = False
        db_table = 'grader_gradingresult'

    def __str__(self) -> str:
        return f"GradingResult(attempt_id={self.attempt_id}, grade={self.grade!r})"


class AnswerFeedback(models.Model):
    """One row per graded subjective answer. Stores per-criterion AI feedback."""
    grading_result = models.ForeignKey(
        GradingResult,
        on_delete=models.CASCADE,
        related_name='answer_feedbacks',
        db_column='gradingResultId',
    )
    question_id = models.IntegerField(db_index=True, db_column='questionId')
    total_score = models.FloatField(db_column='totalScore')
    max_score = models.FloatField(db_column='maxScore')
    flag = models.CharField(max_length=30, blank=True, default='')
    flag_reason = models.TextField(blank=True, default='', db_column='flagReason')
    # JSON: list of {criterion, awarded, max, justification}
    criteria_feedback = models.JSONField(default=list, db_column='criteriaFeedback')
    bedrock_error = models.BooleanField(default=False, db_column='bedrockError')

    class Meta:
        managed = False
        db_table = 'grader_answerfeedback'

    def __str__(self) -> str:
        return f"AnswerFeedback(question_id={self.question_id}, score={self.total_score}/{self.max_score})"
