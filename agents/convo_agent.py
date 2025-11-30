# agents/convo_agent.py
"""
ConversationalAgent: Gemini wrapper + memory-first responder for the Medication Buddy demo.

Features:
- memory-first responses (search + summarize)
- robust Gemini wrapper with safe fallbacks and truncation handling
- upload document processing -> suggested specialties
- send_reminder_and_record demo flow (simulated user reply)
- doctor mode to add advice to patient memory
- small helper getters for recent adherence events
"""

from dotenv import load_dotenv
load_dotenv()

import os
import json
import time
import requests
import re
from typing import List, Dict, Any, Optional

from memory.memory_bank import MemoryBank
from logs.json_logger import JSONLogger
from tools.medcheck_tool import medcheck
from tools.docs_processor import extract_keywords

DEFAULT_MAX_OUTPUT_TOKENS = 512  # conservative default; raise if you need longer model replies


class ConversationalAgent:
    def __init__(self, memory: Optional[MemoryBank] = None, logger: Optional[JSONLogger] = None):
        # Config / environment
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        # endpoint base (no trailing /models), we'll append model path
        self.GEMINI_ENDPOINT = os.getenv("GEMINI_ENDPOINT", "https://generativelanguage.googleapis.com/v1beta")
        self.GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.5-pro")

        # runtime helpers
        self.memory = memory or MemoryBank("memory/memory_bank.json")
        self.logger = logger

    # -----------------------
    # Gemini API wrapper
    # -----------------------
    def call_gemini(self, prompt: str, max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS, temperature: float = 0.2) -> str:
        """
        Call Gemini generateContent for configured model.
        Returns a string (model output) or a deterministic fallback message on error.
        """
        if not self.GEMINI_API_KEY:
            return "SIMULATED MODEL RESPONSE: " + (prompt[:200] + "...")

        base = self.GEMINI_ENDPOINT.rstrip("/")
        model = getattr(self, "GEMINI_MODEL", "models/gemini-2.5-pro")
        url = f"{base}/{model}:generateContent"

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.GEMINI_API_KEY
        }

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_output_tokens,
                "candidateCount": 1
            }
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
        except Exception as e:
            if self.logger:
                self.logger.error({"agent": "convo", "action": "call_gemini_request_failed", "error": str(e)})
            return "SIMULATED MODEL RESPONSE (request error)."

        # parse response safely
        body_json = None
        body_text = ""
        try:
            body_json = resp.json()
        except Exception:
            body_text = resp.text or ""

        if self.logger:
            self.logger.info({
                "agent": "convo",
                "action": "call_gemini_response",
                "status": resp.status_code,
                "body": str(body_json)[:4000] if body_json else body_text[:2000]
            })

        if resp.status_code != 200 or not body_json:
            if self.logger:
                self.logger.error({
                    "agent": "convo",
                    "action": "call_gemini_non200",
                    "status": resp.status_code,
                    "body": str(body_json)[:2000] if body_json else body_text[:2000]
                })
            return "SIMULATED MODEL RESPONSE (API error). See logs."

        # helper to extract model text from known response shapes
        def extract_text(d: Dict[str, Any]) -> Optional[str]:
            try:
                candidates = d.get("candidates") or []
                if candidates:
                    c0 = candidates[0]
                    content = c0.get("content") or {}
                    parts = content.get("parts") or []
                    if parts:
                        first = parts[0]
                        if isinstance(first, dict) and "text" in first:
                            return first["text"]
                        if isinstance(first, str):
                            return first
                    if isinstance(c0.get("output"), str):
                        return c0.get("output")
                if "output_text" in d and isinstance(d["output_text"], str):
                    return d["output_text"]
                if "messages" in d:
                    texts = []
                    for m in d.get("messages", []):
                        for c in (m.get("content") or []):
                            if isinstance(c, dict) and "text" in c:
                                texts.append(c["text"])
                    if texts:
                        return "\n".join(texts)
            except Exception:
                return None
            return None

        out = extract_text(body_json)

        # detect truncation metadata (finishReason == MAX_TOKENS)
        try:
            cand0 = (body_json.get("candidates") or [None])[0]
            if cand0 and isinstance(cand0, dict) and cand0.get("finishReason") == "MAX_TOKENS":
                if out:
                    return out + "\n\n---\n(Note: model truncated by MAX_TOKENS; consider raising max_output_tokens)"
                else:
                    if self.logger:
                        self.logger.info({"agent": "convo", "action": "model_truncated_candidate", "candidate": json.dumps(cand0)[:2000]})
                    return "MODEL_TRUNCATED: Increase max_output_tokens. Partial candidate logged."
        except Exception:
            pass

        if out:
            return out

        if self.logger:
            self.logger.error({"agent": "convo", "action": "call_gemini_unparseable", "body": str(body_json)[:2000]})
        return "SIMULATED MODEL RESPONSE (unparseable). See logs."

    # -----------------------
    # Memory helpers
    # -----------------------
    def search_memory(self, user_id: str, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Very simple keyword search across JSON-serializable events.
        Returns matches (newest first) where any token appears in the JSON string of the event.
        """
        events = self.memory.get_user_memory(user_id)
        if not events:
            return []
        q_tokens = [t.lower() for t in re.findall(r"\w+", query) if len(t) > 2][:10]
        if not q_tokens:
            return []
        matches: List[Dict[str, Any]] = []
        for ev in reversed(events):  # newest first
            s = json.dumps(ev).lower()
            for t in q_tokens:
                if t in s:
                    matches.append(ev)
                    break
            if len(matches) >= max_results:
                break
        return matches

    def summarize_events(self, events: List[Dict[str, Any]], concise: bool = True) -> str:
        """
        Local summarization of events into readable bullets. If many events and concise=False,
        optionally call model to compress further.
        """
        if not events:
            return ""
        bullets: List[str] = []
        for ev in events:
            tp = ev.get("type", "event")
            if tp == "adherence_event":
                med = ev.get("med") or ev.get("med_name") or ""
                ts = ev.get("timestamp") or ev.get("recorded_at") or ev.get("time") or ""
                try:
                    human_ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(float(ts)))
                except Exception:
                    human_ts = str(ts)
                bullets.append(f"- Took {med} at {human_ts}")
            elif tp == "uploaded_doc_summary":
                meds = ", ".join([k for k in ev.get("keywords", [])[:6]])
                specs = ", ".join(ev.get("suggested_specialties", []))
                bullets.append(f"- Uploaded doc keywords: {meds}. Suggested: {specs}")
            elif tp == "doctor_advice":
                adv = ev.get("advice_text", "")
                doc = ev.get("doctor_id", "doctor")
                bullets.append(f"- Doctor {doc} advised: {adv}")
            else:
                bullets.append(f"- {tp}: {str(ev)[:120]}")

        summary = "\n".join(bullets[:20])
        if len(bullets) > 20 and not concise:
            # ask model to compress into 3 lines
            prompt = "Summarize these patient events into 3 concise lines:\n\n" + summary
            model_out = self.call_gemini(prompt, max_output_tokens=200)
            return model_out or summary
        return summary

    # -----------------------
    # Memory-first responder
    # -----------------------
    def respond_with_memory_first(self, user_id: str, query: str) -> str:
        """
        1) Search memory for matches to the query
        2) If matches exist, return a short local summary and offer to expand
        3) If none found, call Gemini directly
        """
        if self.logger:
            self.logger.info({"agent": "convo", "action": "respond_with_memory_first", "user": user_id, "query": query})
        matches = self.search_memory(user_id, query, max_results=8)
        if matches:
            summary = self.summarize_events(matches, concise=True)
            if not summary.strip():
                if self.logger:
                    self.logger.info({"agent": "convo", "action": "empty_summary_fallback"})
                return self.call_gemini(query)
            return f"I found these saved notes related to your question:\n\n{summary}\n\nIf you want more details I can expand or ask the model to interpret these."
        # nothing in memory
        return self.call_gemini(query)

    # -----------------------
    # App features
    # -----------------------
    def send_reminder_and_record(self, user_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sends a reminder prompt to the model, simulates user reply (demo), and logs adherence event.
        event keys: 'med' or 'med_name', optionally 'dose'/'dosage', 'time', 'frequency'
        """
        med = event.get("med") or event.get("med_name") or "medication"
        dose = event.get("dose") or event.get("dosage") or ""
        prompt = f"Reminder: It's time to take {med} {dose}. Ask the user to confirm 'Did you take {med}?' and handle yes/no."
        if self.logger:
            self.logger.info({"agent": "convo", "action": "send_reminder", "user": user_id, "med": med})
        model_resp = self.call_gemini(prompt)
        # Demo: simulate user confirming
        user_reply = "Yes, I took it."
        timestamp = time.time()
        entry = {
            "type": "adherence_event",
            "user_id": user_id,
            "med": med,
            "dose": dose,
            "timestamp": timestamp,
            "user_reply": user_reply,
            "recorded_at": timestamp
        }
        self.memory.append_user_event(user_id, entry)
        return {"model_response": model_resp, "user_reply": user_reply, "saved": True}

    def handle_uploaded_document(self, user_id: str, doc_text: str) -> List[str]:
        """
        Process uploaded prescription/medical record text, extract keywords/conditions,
        recommend specialties. Robust to model errors/truncation.
        """
        keywords = extract_keywords(doc_text)
        specialty_map = {
            "chest pain": ["Cardiology"],
            "shortness of breath": ["Pulmonology", "Cardiology"],
            "high blood pressure": ["Cardiology", "Internal Medicine"],
            "diabetes": ["Endocrinology", "Internal Medicine"],
            "elevated lipids": ["Cardiology", "Endocrinology"],
            "fracture": ["Orthopedics"],
            "skin rash": ["Dermatology"],
            "abdominal pain": ["Gastroenterology"]
        }

        suggested = set()
        # rule-based matching first
        for kw in keywords:
            for token, specs in specialty_map.items():
                if token in kw.lower():
                    suggested.update(specs)

        if not suggested:
            # fallback to the model to infer specialties
            prompt = f"Given these extracted keywords from a medical record: {keywords[:20]}, suggest likely medical specialties a patient should visit."
            model_suggestions = self.call_gemini(prompt, max_output_tokens=200)

            # defensive checks for sentinel/error messages
            ms_text = str(model_suggestions or "")
            if not ms_text.strip() or any(sig in ms_text.upper() for sig in ("MODEL_TRUNCATED", "SIMULATED MODEL RESPONSE", "API ERROR", "UNPARSEABLE")):
                if self.logger:
                    self.logger.info({"agent": "convo", "action": "handle_uploaded_document_fallback", "user": user_id, "model_resp": ms_text[:500]})
                suggested.update(["Primary Care", "Internal Medicine"])
            else:
                # parse sensible items by splitting common separators
                parts = [p.strip() for p in re.split(r"[,\n;]+", ms_text) if len(p.strip()) > 2]
                for p in parts[:6]:
                    suggested.add(p)

        summary_entry = {
            "type": "uploaded_doc_summary",
            "user_id": user_id,
            "keywords": keywords,
            "suggested_specialties": list(suggested),
            "raw_excerpt": doc_text[:500],
            "recorded_at": time.time()
        }
        self.memory.append_user_event(user_id, summary_entry)

        if self.logger:
            self.logger.info({"agent": "convo", "action": "doc_processed", "user": user_id, "specialties": list(suggested)})

        return list(suggested)

    def doctor_add_advice(self, user_id: str, doctor_id: str, advice_text: str, related_specialties: Optional[List[str]] = None) -> bool:
        """
        Doctor mode: add an advice note to patient memory.
        """
        note = {
            "type": "doctor_advice",
            "user_id": user_id,
            "doctor_id": doctor_id,
            "advice_text": advice_text,
            "related_specialties": related_specialties or [],
            "timestamp": time.time(),
            "recorded_at": time.time()
        }
        self.memory.append_user_event(user_id, note)
        if self.logger:
            self.logger.info({"agent": "convo", "action": "doctor_add_advice", "user": user_id, "doctor_id": doctor_id})
        return True

    # convenience getter
    def get_recent_adherence(self, user_id: str, n: int = 5) -> List[Dict[str, Any]]:
        evs = list(reversed(self.memory.get_user_memory(user_id)))
        return [e for e in evs if e.get("type") == "adherence_event"][:n]
