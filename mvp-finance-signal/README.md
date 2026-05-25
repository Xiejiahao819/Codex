# Finance Signal MVP (FastAPI Scaffold)

## Run

```bash
cd mvp-finance-signal
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Test

```bash
cd mvp-finance-signal
PYTHONPATH=. pytest -q
```
