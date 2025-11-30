import os
import json
import time
from pathlib import Path

from agents.convo_agent import ConversationalAgent
from memory.memory_bank import MemoryBank
from logs.json_logger import JSONLogger

ROOT = Path(__file__).resolve().parents[1]
logger = JSONLogger(ROOT / "logs" / "logs.jsonl")
memory = MemoryBank(str(ROOT / "memory" / "memory_bank.json"))
agent = ConversationalAgent(memory=memory, logger=logger)

UID = "cli-user"


def interactive_reminder_flow():
    print("Let's set a reminder.")
    med = input("Medicine name (e.g. Metformin 500mg): ").strip()
    if not med:
        print("Cancelled: medicine name is required.")
        return
    time_str = input("Time (e.g. 08:00 or 'in 1 minute'): ").strip()
    if not time_str:
        print("Cancelled: time is required.")
        return
    frequency = input("Frequency (e.g. once, daily, twice a day): ").strip() or "once"
    # Simple event object saved to memory. Scheduling not implemented here.
    event = {"med": med, "time": time_str, "frequency": frequency}
    resp = agent.send_reminder_and_record(UID, event)
    print("Reminder recorded. Agent response:")
    print(resp["model_response"])
    # simulate immediate follow-up: show stored memory snippet
    print("Saved to memory. Recent adherence entries:")
    # use get_user_memory instead of deprecated get_user_events
    entries = memory.get_user_memory(UID)[-6:]
    print(json.dumps(entries, indent=2))


def simulate_doc_upload():
    sample_path = ROOT / "sample_data" / "prescription_sample.pdf"
    if sample_path.exists():
        # use fallback text file if present for deterministic tests
        txt_path = sample_path.with_suffix(".txt")
        doc_text = txt_path.read_text() if txt_path.exists() else "Simulated prescription: Metformin 500mg twice daily, Atorvastatin 10mg once nightly."
    else:
        doc_text = "Simulated prescription: Metformin 500mg twice daily, Atorvastatin 10mg once nightly."

    specs = agent.handle_uploaded_document(UID, doc_text)

    # Read the last uploaded_doc_summary we just added
    events = memory.get_user_memory(UID)
    last_doc = None
    for ev in reversed(events):
        if ev.get("type") == "uploaded_doc_summary":
            last_doc = ev
            break

    print("Agent suggested specialties:", specs)
    if last_doc:
        print("\nDetailed summary saved to memory:")
        print("  Extracted keywords:", last_doc.get("keywords"))
        print("  Suggested specialties:", last_doc.get("suggested_specialties"))
        print("  Raw excerpt (truncated):")
        print("  ", last_doc.get("raw_excerpt"))
    else:
        print("No uploaded_doc_summary found in memory. Something went wrong.")



def simulate_doctor_advice():
    doc_id = input("Doctor id (e.g. dr-1): ").strip() or "dr-1"
    advice = input("Advice text: ").strip() or "Check blood sugar more frequently and adjust dose."
    specs = input("Related specialties (comma separated): ").strip()
    related = [s.strip() for s in specs.split(",")] if specs else []
    ok = agent.doctor_add_advice(UID, doc_id, advice, related)
    print("Doctor advice saved:", ok)


print("Type 'exit' to quit.")
print("Commands: 'remind' (or 'remind me ...'), 'test reminder', 'doc', 'doctor', or free chat text to forward to the agent.")
while True:
    try:
        q = input("You: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nbye")
        break
    if not q:
        continue
    if q.lower() in ("exit", "quit"):
        break

    # Simple command routing
    low = q.lower()
    if "remind" in low:
        interactive_reminder_flow()
        continue
    if low.startswith("test reminder") or low.startswith("test"):
        print("This is your test reminder!")
        continue
    if low.startswith("doc"):
        simulate_doc_upload()
        continue
    if low.startswith("doctor"):
        simulate_doctor_advice()
        continue

    # Default: go through memory-first responder
    resp = agent.respond_with_memory_first(UID, q)
    print("Agent:", resp)
    # store chat in memory for traceability
    memory.append_user_event(UID, {"type": "cli_chat", "user_id": UID, "prompt": q, "response": str(resp), "ts": time.time()})
