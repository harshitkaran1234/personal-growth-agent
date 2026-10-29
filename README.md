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

## Checks

```bash
poetry run pytest
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
tests/
```

`ENVIRONMENT` selects the env file: unset or anything else loads `.env`, `dev*` loads `.dev.env`,
`staging*` loads `.staging.env`.
