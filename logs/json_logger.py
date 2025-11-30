# logs/json_logger.py
"""
Simple structured JSON logger that appends one JSON object per line.
"""

import json
import time
import os

class JSONLogger:
    def __init__(self, filepath="logs/logs.jsonl"):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.filepath = filepath

    def info(self, obj):
        self._write({"level":"info","ts": time.time(), **obj})

    def error(self, obj):
        self._write({"level":"error","ts": time.time(), **obj})

    def _write(self, o):
        with open(self.filepath, "a") as f:
            f.write(json.dumps(o) + "\n")
