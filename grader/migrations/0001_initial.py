from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='GradingResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attempt_id', models.IntegerField(db_index=True, unique=True)),
                ('assessment_id', models.IntegerField(db_index=True)),
                ('score', models.FloatField()),
                ('grade', models.CharField(max_length=10)),
                ('plagiarism_flagged', models.BooleanField(default=False)),
                ('graded_at', models.DateTimeField(auto_now_add=True)),
                ('error_notes', models.TextField(blank=True, default='')),
            ],
        ),
        migrations.CreateModel(
            name='AnswerFeedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('grading_result', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='answer_feedbacks',
                    to='grader.gradingresult',
                )),
                ('question_id', models.IntegerField(db_index=True)),
                ('total_score', models.FloatField()),
                ('max_score', models.FloatField()),
                ('flag', models.CharField(blank=True, default='', max_length=30)),
                ('flag_reason', models.TextField(blank=True, default='')),
                ('criteria_feedback', models.JSONField(default=list)),
                ('bedrock_error', models.BooleanField(default=False)),
            ],
        ),
    ]
