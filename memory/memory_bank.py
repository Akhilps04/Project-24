# memory/memory_bank.py
"""
Simple file-backed MemoryBank that stores events per user.
Each append writes to disk (append-only) and in-memory index is kept for quick access.
"""

import json
import os
import time

class MemoryBank:
    def __init__(self, path="memory/memory_bank.json"):
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            with open(self.path, "w") as f:
                json.dump({}, f)
        self._load()

    def _load(self):
        with open(self.path, "r") as f:
            try:
                self.store = json.load(f)
            except Exception:
                self.store = {}

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self.store, f, indent=2)

    def append_user_event(self, user_id, event):
        self.store.setdefault(user_id, [])
        event = dict(event)
        event.setdefault("recorded_at", time.time())
        self.store[user_id].append(event)
        self._save()

    def get_user_memory(self, user_id):
        return self.store.get(user_id, [])

    def get_user_events(self, user_id):
        """
        Return a list of events for the given user_id.
        Works even if the JSON file structure changes in the future.
        """
        try:
            # load fresh from disk
            with open(self.path, "r") as f:
                raw = f.read().strip()
                if not raw:
                    return []

                data = json.loads(raw)

            # Case A: normal dict {user_id: [events]}
            if isinstance(data, dict) and user_id in data and isinstance(data[user_id], list):
                return data[user_id]

            # Case B: flat list of events
            if isinstance(data, list):
                return [e for e in data if isinstance(e, dict) and e.get("user_id") == user_id]

            # Case C: nested dict lists
            results = []
            if isinstance(data, dict):
                for v in data.values():
                    if isinstance(v, list):
                        for e in v:
                            if isinstance(e, dict) and e.get("user_id") == user_id:
                                results.append(e)
            return results

        except Exception:
            return []


    def clear_user_memory(self, user_id):
        if user_id in self.store:
            del self.store[user_id]
            self._save()
            return True
        return False
