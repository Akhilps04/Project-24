# agents/calendar_agent.py
"""
CalendarAgent: simple scheduler storing events in-memory and persisted file.
Provides get_due_events(simulate_now=True) for demo.
"""

import json
from datetime import datetime, time
from dateutil import parser as dateparser
import os

class CalendarAgent:
    def __init__(self, memory=None, logger=None, store_path=None):
        base = os.path.dirname(os.path.dirname(__file__))
        self.store_path = store_path or os.path.join(base, "memory", "schedule_store.json")
        self.memory = memory
        self.logger = logger
        self._load_store()

    def _load_store(self):
        try:
            with open(self.store_path, "r") as f:
                self.store = json.load(f)
        except Exception:
            self.store = {}

    def _save_store(self):
        with open(self.store_path, "w") as f:
            json.dump(self.store, f, indent=2)

    def schedule_user_meds(self, user_id, meds):
        """
        meds: list of {name, dose, time (HH:MM)}
        """
        self.store.setdefault(user_id, [])
        for m in meds:
            ev = {
                "id": f"{user_id}-{m['name']}-{m['time']}",
                "med": m['name'],
                "dose": m.get("dose"),
                "time": m.get("time")
            }
            self.store[user_id].append(ev)
        self._save_store()
        if self.logger:
            self.logger.info({"event":"schedule_user_meds","user":user_id,"count":len(meds)})

    def get_due_events(self, user_id=None, simulate_now=True):
        """
        Returns events that are due now. simulate_now returns all events to demo flow.
        """
        if simulate_now:
            events = []
            for u, evs in self.store.items():
                for e in evs:
                    events.append({"user_id": u, **e})
            return events
        # Real-time implementation would compare times and return matches.
        return []

