import time
import json
from datetime import datetime


class Logger:
    def __init__(self):
        self.start_time = None
        self.trace = {}

    def start(self):
        self.start_time = time.time()
        self.trace["start_time"] = datetime.utcnow().isoformat()

    def log(self, key, value):
        self.trace[key] = value

    def end(self):
        self.trace["latency_ms"] = round((time.time() - self.start_time) * 1000, 2)
        self.trace["end_time"] = datetime.utcnow().isoformat()
        return self.trace

    def print(self):
        # default=str avoids runtime failures for uncommon non-JSON-native objects.
        print(json.dumps(self.trace, indent=2, default=str))
