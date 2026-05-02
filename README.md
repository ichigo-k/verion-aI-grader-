# verion-ai-grader

A standalone Django microservice that acts as the AI grading engine for the `ai-powered-grading-system`. It connects to the shared PostgreSQL database, grades subjective answers using AWS Bedrock, detects plagiarism via answer hash comparison, and writes scores back to the database.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- PostgreSQL (shared with the main system)
- AWS credentials with Bedrock access

## Setup

### 1. Clone and install dependencies

```bash
# Install uv if not already installed
pip install uv

# Install all dependencies (including dev)
uv sync --extra dev
```

### 2. Configure environment variables

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with your actual values. See [Environment Variables](#environment-variables) below.

### 3. Run database migrations

This only creates the grader's own tables (`grader_gradingresult`, `grader_answerfeedback`, `auth_keys_apikey`). It does **not** touch any tables owned by the main system.

```bash
uv run python manage.py migrate
```

### 4. Generate an API key

```bash
uv run python manage.py generate_api_key --label "main-system"
```

The plaintext key is printed to stdout **once**. Store it securely — it cannot be recovered. Pass it as the `X-API-Key` header in all requests to this service.

### 5. Run the development server

```bash
uv run python manage.py runserver 0.0.0.0:8000
```

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `DJANGO_SECRET_KEY` | Django secret key (generate with `python -c "import secrets; print(secrets.token_hex(50))"`) |
| `DATABASE_URL` | PostgreSQL connection string, e.g. `postgresql://user:pass@host:5432/dbname` |
| `AWS_ACCESS_KEY_ID` | AWS access key with Bedrock permissions |
| `AWS_SECRET_ACCESS_KEY` | AWS secret access key |
| `AWS_REGION` | AWS region where Bedrock is available, e.g. `us-east-1` |
| `BEDROCK_MODEL_ID` | Bedrock model identifier, e.g. `anthropic.claude-3-sonnet-20240229-v1:0` |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `False` | Set to `True` for development |
| `ALLOWED_HOSTS` | `*` (when DEBUG=True) | Comma-separated list of allowed hostnames |
| `GRADING_SCALE` | `{"A":70,"B":60,"C":50,"D":40}` | JSON object mapping letter grades to minimum percentage thresholds |
| `BEDROCK_MAX_TOKENS` | `2048` | Maximum tokens per Bedrock invocation |
| `GRADING_CONCURRENCY` | `10` | Number of attempts graded in parallel during batch grading |

## API Endpoints

All endpoints require the `X-API-Key` header.

### Batch grade an assessment

```
POST /api/grade/assessment/{assessment_id}/
X-API-Key: <your-api-key>
```

Grades all `SUBMITTED` and `TIMED_OUT` attempts for the assessment. Returns:

```json
{
  "assessment_id": 42,
  "graded_count": 15,
  "grading_status": "GRADED",
  "plagiarism_flags": [
    { "question_id": 7, "flagged_attempt_ids": [3, 9] }
  ]
}
```

### Grade a single attempt

```
POST /api/grade/attempt/{attempt_id}/
X-API-Key: <your-api-key>
```

Returns:

```json
{
  "attempt_id": 17,
  "score": 72.5,
  "grade": "A",
  "plagiarism_flagged": false,
  "answer_feedbacks": [
    {
      "question_id": 3,
      "total_score": 18.0,
      "max_score": 20.0,
      "flag": "none",
      "flag_reason": "",
      "criteria_feedback": [
        { "criterion": "Clarity", "awarded": 8, "max": 10, "justification": "..." }
      ],
      "bedrock_error": false
    }
  ],
  "error_notes": ""
}
```

## Running Tests

```bash
uv run pytest
```

## Docker

See [Dockerfile](./Dockerfile) for containerised deployment.

```bash
docker build -t verion-ai-grader .
docker run -p 8000:8000 --env-file .env verion-ai-grader
```
