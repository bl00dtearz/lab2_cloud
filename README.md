# Lab 2 - REST API and Message Queues

REST service (Flask) with a file-based message queue (variant C-2, no AWS) and a separate worker.
The full specification is in [spec.md](spec.md).

https://github.com/bl00dtearz/lab2_cloud.git

## Files

| File | Purpose |
|------|---------|
| spec.md | Service specification (written and committed before the code) |
| app.py | REST API: /echo, /time, /jobs, /jobs/<job_id> |
| worker.py | Worker: takes jobs from `queue/`, processes them, saves results to `results/` |
| requirements.txt | Python packages |
| report.pdf | Answers to the questions and screenshots |

## Run

```
python -m venv venv
venv\Scripts\activate         
pip install -r requirements.txt

# terminal 1 - API on http://127.0.0.1:5000
python app.py

# terminal 2 - worker
python worker.py
```

## Try it (PowerShell)

```
Invoke-RestMethod -Uri http://127.0.0.1:5000/echo -Method POST -ContentType "application/json" -Body '{"message":"hello"}'
Invoke-RestMethod -Uri http://127.0.0.1:5000/time

curl.exe -i -X POST http://127.0.0.1:5000/echo -H "Content-Type: application/json" -d "{}"
curl.exe -i http://127.0.0.1:5000/nope

Invoke-RestMethod -Uri http://127.0.0.1:5000/jobs -Method POST -ContentType "application/json" -Body '{"message":"hello world"}'
curl.exe -i http://127.0.0.1:5000/jobs/<job_id>
```

Job status is `queued` right after submission and `done` (with `result`) 2-3 seconds later.

## Notes

- The worker deletes a job file only after the result is saved.
- A malformed job file is moved to `queue/failed/`.
- `queue/`, `results/`, `venv/` are not committed (see .gitignore).
