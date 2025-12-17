# ml

A Python Polylith project template

```bash
uv init
uv add python-polylith
poly init
uv sync
```


```bash
cp .env.example .env

PYTHONPATH="components:bases:$PYTHONPATH" uv run uvicorn ml.leaderboard_api.core:app --reload

PYTHONPATH="components:bases:$PYTHONPATH" uv run uvicorn ml.leaderboard_api.core:app --host 0.0.0.0 --port 8000

uv run pytest test/
```