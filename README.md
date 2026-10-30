# personal-growth-agent

Backend for the Personal Growth Agent: an AI coach that helps people set goals, keep weekly
commitments and see their progress. FastAPI + Poetry, Python 3.12.

## Setup

```bash
poetry install
cp .env.example .env
```

## Run

```bash
poetry run python -m personal_growth_agent.script.server
# http://localhost:8000/health
# http://localhost:8000/docs
```

Needs MongoDB on `localhost:27017` (or set `MONGO_CONNECTION_URI`).

## Login

Email OTP. Until AWS SES is integrated, `HARDCODED_OTP=123456` in `.env` makes every code
`123456` and no email is sent. The app refuses to start with it set when
`ENVIRONMENT=production`.

```bash
curl -X POST localhost:8000/v1/auth/email/otp -H 'content-type: application/json' \
  -d '{"email":"you@example.com"}'
curl -X POST localhost:8000/v1/auth/email/otp/validate -H 'content-type: application/json' \
  -d '{"email":"you@example.com","otp":"123456"}'
# use the returned access_token: Authorization: Bearer <token>
curl localhost:8000/v1/user/me -H 'Authorization: Bearer <token>'
```

## Checks

```bash
poetry run black .
poetry run flake8
poetry run mypy personal_growth_agent
```

## Layout

```
personal_growth_agent/
  main.py              app factory, middleware, exception handlers
  common/              config, logger, exceptions, exception handlers
  routes/              one folder per resource (route.py + controller.py)
  schema/              request and response models
  script/server.py     local dev server
```

`ENVIRONMENT` selects the env file: unset or anything else loads `.env`, `dev*` loads `.dev.env`,
`staging*` loads `.staging.env`.
