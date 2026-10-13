Service Specification - Lab 2

Author: Musagaliev Rakhat

1. Purpose

A small REST service for students and testers that echoes messages, returns the current server time, and accepts long-running text-processing jobs through a message queue. The client gets a job identifier immediately and checks the result later.

2. Endpoints
No	Method	Path	Input (JSON)	Output (JSON)	Response codes
R1	POST	/echo	{"message": string}	{"reply": string}	200, 400
R2	GET	/time	-	{"time": string, ISO 8601 UTC, e.g. "2026-10-13T10:15:00+00:00"}	200
R3	POST	/jobs	{"message": string}	{"job_id": string (UUID), "status": "queued"}	202, 400
R4	GET	/jobs/<job_id>	-	{"job_id": string, "status": "queued" or "done", "result": string or null}	200, 404
R5	any	unknown path	-	{"error": string}	404
R6	-	worker	job file from the queue	result file results/<job_id>.json; bad job file moved to queue/failed/	-

Errors and edge cases:

Body is not valid JSON, is empty, or has no "message" field: 400 with {"error": "field 'message' is required"}.
"message" is not a string or is an empty string: 400 with {"error": "'message' must be a non-empty string"}.
"message" longer than 1000 characters: 400 with {"error": "'message' is too long (max 1000)"}.
job_id is not a valid UUID, or no queue file and no result exist for it: 404 with {"error": "job not found"}.
Wrong HTTP method on a known path: 405 with {"error": "method not allowed"}.
Any unexpected server error: 500 with {"error": "internal server error"}; the service does not crash.
3. Queue message format

The API writes one JSON file queue/<job_id>.json (first as .tmp, then renamed atomically):

Field	Type	Description
job_id	string (UUID v4)	unique job identifier
message	string	text to process (1-1000 chars)

Result file results/<job_id>.json:

Field	Type	Description
job_id	string	same identifier
result	string	the message converted to upper case

Malformed message behavior (R6): if the worker cannot parse a queue file or it has no valid "job_id"/"message", the worker logs the problem, moves the file to queue/failed/ and continues. The worker never stops because of one bad file.

Status rule for R4: done if results/<job_id>.json exists; otherwise queued if queue/<job_id>.json exists; otherwise 404.

4. Constraints
Protocol: HTTP/1.1, data format: JSON (UTF-8).
Host and port: 127.0.0.1:5000.
Python 3.10 or newer; packages: Flask (see requirements.txt).
Queue service: variant C-2, file-based queue (folder queue/, no AWS).
Worker is a separate process: python worker.py in a second terminal.
Run: pip install -r requirements.txt, then python app.py and python worker.py.
No secrets in code or in the archive.

5. Non-functional requirements (with numbers)
N1: /echo and /time answer in under 200 ms (95th percentile) with 10 concurrent users. Check: a small Python script with 10 threads x 50 requests, measure time per request.
N2: POST /jobs returns 202 in under 200 ms even while the worker is busy (the 2-second work is not in the request). Check: measure the response time of 20 consecutive POST /jobs.
N3: with an empty queue, a job reaches status "done" within 5 seconds after submission (2 s processing + 1 s polling + margin). Check: submit a job and poll R4 every 0.5 s, record the time until "done".
N4: no request with an invalid job_id (not a UUID) can read files outside results/ and queue/. Check: send GET /jobs/..%2Fapp.py and GET /jobs/test; both must return 404.
N5: the service must not crash on invalid input. Check: 10 bad requests (empty body, wrong types, huge message) give 400, and the next valid request still returns 200.

6. Assumptions
A1: The disk is writable and has free space. Risk: if not, POST /jobs fails with 500 and the job is lost. Decision: errors on writing the queue file are caught and return 500, not 202.
A2: Only one worker process runs at a time. Risk: two workers could take the same file and process a job twice. Decision: the worker is started once; delivery is "at least once" and processing is idempotent (same input gives same result file).
A3: Messages are short text (up to 1000 characters). Risk: huge bodies slow the service. Decision: the API rejects longer messages with 400.
A4: The API and the worker run on the same machine and share the folders queue/ and results/. Risk: on different machines the status endpoint would not see results. Decision: for this lab one machine is enough; for Lab 5 the folder queue would be replaced by SQS.
A5: Results are kept only for testing and are not deleted automatically. Risk: the results/ folder grows. Decision: acceptable for the lab; cleaned manually.