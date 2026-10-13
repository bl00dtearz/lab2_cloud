import glob
import json
import os
import shutil
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUEUE_DIR = os.path.join(BASE_DIR, "queue")
FAILED_DIR = os.path.join(QUEUE_DIR, "failed")
RESULTS_DIR = os.path.join(BASE_DIR, "results")

os.makedirs(QUEUE_DIR, exist_ok=True)
os.makedirs(FAILED_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)


def move_to_failed(path, reason):
    print(f"[worker] bad job file {os.path.basename(path)}: {reason} -> queue/failed/")
    try:
        shutil.move(path, os.path.join(FAILED_DIR, os.path.basename(path)))
    except OSError as e:
        print(f"[worker] could not move file: {e}")


def process(path):

    try:
        with open(path, encoding="utf-8") as f:
            body = json.load(f)
        job_id = body["job_id"]
        message = body["message"]
        if not isinstance(job_id, str) or not isinstance(message, str):
            raise ValueError("job_id and message must be strings")
    except (OSError, ValueError, KeyError, TypeError) as e:
        move_to_failed(path, repr(e))
        return

    print(f"[worker] processing job {job_id}")
    time.sleep(2)  

    result = message.upper()

    result_path = os.path.join(RESULTS_DIR, f"{job_id}.json")
    tmp_path = result_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump({"job_id": job_id, "result": result}, f)
    os.replace(tmp_path, result_path)

    os.remove(path)
    print(f"[worker] job {job_id} done")


def main():
    print("[worker] started, watching queue/ (Ctrl+C to stop)")
    while True:
        files = sorted(glob.glob(os.path.join(QUEUE_DIR, "*.json")))
        if not files:
            time.sleep(1)
            continue
        try:
            process(files[0])
        except Exception as e: 
            print(f"[worker] unexpected error: {e!r}")
            time.sleep(1)


if __name__ == "__main__":
    main()
