"""
No-op initial migration for the grader app.

All models in the grader app use managed=False — their tables are either:
  - Owned by the main system (ai-powered-grading-system via Prisma): assessments,
    assessment_sections, assessment_attempts, questions, rubric_criteria, student_answers
  - Owned by Prisma but written by this service: grader_gradingresult, grader_answerfeedback

Django will never run CREATE, ALTER, or DROP against any of these tables.
This migration exists only to satisfy Django's migration framework and prevent
makemigrations from generating spurious migrations for managed=False models.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        # All CreateModel operations below are no-ops because managed=False.
        # They exist solely to record the model state so makemigrations
        # does not generate a new migration on every run.
        migrations.CreateModel(
            name="Assessment",
            fields=[
                ("id", models.IntegerField(primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=255)),
                ("total_marks", models.IntegerField(db_column="totalMarks")),
                ("grading_status", models.CharField(db_column="gradingStatus", max_length=20)),
                ("status", models.CharField(max_length=20)),
            ],
            options={"db_table": "assessments", "managed": False},
        ),
        migrations.CreateModel(
            name="AssessmentSection",
            fields=[
                ("id", models.IntegerField(primary_key=True, serialize=False)),
                ("assessment_id", models.IntegerField(db_column="assessmentId")),
                ("type", models.CharField(max_length=20)),
            ],
            options={"db_table": "assessment_sections", "managed": False},
        ),
        migrations.CreateModel(
            name="AssessmentAttempt",
            fields=[
                ("id", models.IntegerField(primary_key=True, serialize=False)),
                ("assessment_id", models.IntegerField(db_column="assessmentId")),
                ("student_id", models.IntegerField(db_column="studentId")),
                ("status", models.CharField(max_length=20)),
                ("score", models.FloatField(blank=True, null=True)),
            ],
            options={"db_table": "assessment_attempts", "managed": False},
        ),
        migrations.CreateModel(
            name="Question",
            fields=[
                ("id", models.IntegerField(primary_key=True, serialize=False)),
                ("assessment_id", models.IntegerField(db_column="assessmentId")),
                ("section_id", models.IntegerField(db_column="sectionId")),
                ("body", models.TextField()),
                ("marks", models.IntegerField()),
                ("answer_type", models.CharField(blank=True, db_column="answerType", max_length=20, null=True)),
            ],
            options={"db_table": "questions", "managed": False},
        ),
        migrations.CreateModel(
            name="RubricCriterion",
            fields=[
                ("id", models.IntegerField(primary_key=True, serialize=False)),
                ("question_id", models.IntegerField(db_column="questionId")),
                ("description", models.TextField()),
                ("max_marks", models.IntegerField(db_column="maxMarks")),
                ("order", models.IntegerField()),
            ],
            options={"db_table": "rubric_criteria", "managed": False},
        ),
        migrations.CreateModel(
            name="StudentAnswer",
            fields=[
                ("id", models.IntegerField(primary_key=True, serialize=False)),
                ("attempt_id", models.IntegerField(db_column="attemptId")),
                ("question_id", models.IntegerField(db_column="questionId")),
                ("answer_text", models.TextField(blank=True, db_column="answerText", null=True)),
                ("file_url", models.TextField(blank=True, db_column="fileUrl", null=True)),
                ("answer_hash", models.CharField(blank=True, db_column="answerHash", max_length=64, null=True)),
            ],
            options={"db_table": "student_answers", "managed": False},
        ),
        migrations.CreateModel(
            name="GradingResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("attempt_id", models.IntegerField(db_column="attemptId", db_index=True, unique=True)),
                ("assessment_id", models.IntegerField(db_column="assessmentId", db_index=True)),
                ("score", models.FloatField()),
                ("plagiarism_flagged", models.BooleanField(db_column="plagiarismFlagged", default=False)),
                ("graded_at", models.DateTimeField(db_column="gradedAt")),
                ("error_notes", models.TextField(blank=True, db_column="errorNotes", default="")),
            ],
            options={"db_table": "grader_gradingresult", "managed": False},
        ),
        migrations.CreateModel(
            name="AnswerFeedback",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("question_id", models.IntegerField(db_column="questionId", db_index=True)),
                ("total_score", models.FloatField(db_column="totalScore")),
                ("max_score", models.FloatField(db_column="maxScore")),
                ("flag", models.CharField(blank=True, default="", max_length=30)),
                ("flag_reason", models.TextField(blank=True, db_column="flagReason", default="")),
                ("criteria_feedback", models.JSONField(db_column="criteriaFeedback", default=list)),
                ("bedrock_error", models.BooleanField(db_column="bedrockError", default=False)),
            ],
            options={"db_table": "grader_answerfeedback", "managed": False},
        ),
    ]
