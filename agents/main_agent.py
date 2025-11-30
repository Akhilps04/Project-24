# agents/main_agent.py
"""
Demo driver for Medication Buddy with prescription upload + specialist recommendation.
Usage:
  python -m agents.main_agent --demo
"""

import argparse
import os
import json
from agents.calendar_agent import CalendarAgent
from agents.convo_agent import ConversationalAgent
from tools.medcheck_tool import medcheck
from tools.docs_processor import process_document
from memory.memory_bank import MemoryBank
from logs.json_logger import JSONLogger

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))

def demo():
    logger = JSONLogger(os.path.join(ROOT_DIR, "logs", "logs.jsonl"))
    memory = MemoryBank(os.path.join(ROOT_DIR, "memory", "memory_bank.json"))
    cal = CalendarAgent(memory=memory, logger=logger)
    convo = ConversationalAgent(memory=memory, logger=logger)

    # Example user and meds
    user_id = "user-1"
    meds = [
        {"name": "Atorvastatin", "dose": "10mg", "time": "08:00"},
        {"name": "Metformin", "dose": "500mg", "time": "08:00"}
    ]

    print("Scheduling meds for demo user...")
    cal.schedule_user_meds(user_id, meds)
    logger.info({"event": "scheduled_meds", "user": user_id, "meds": meds})

    # Simulate a prescription upload (replace with real file path to test)
    sample_prescription = os.path.join(ROOT_DIR, "sample_data", "prescription_sample.pdf")
    if os.path.exists(sample_prescription):
        print("Processing uploaded prescription:", sample_prescription)
        doc_text = process_document(sample_prescription)
        logger.info({"event": "doc_processed", "user": user_id, "summary": doc_text[:300]})
        convo.handle_uploaded_document(user_id, doc_text)
    else:
        print("No sample prescription found at", sample_prescription)
        print("You can still run reminder simulation.")

    # Simulate due reminders
    print("Fetching due events (simulated)...")
    events = cal.get_due_events(simulate_now=True)
    for ev in events:
        flags = medcheck(meds)
        if flags:
            logger.info({"event": "medcheck_flags", "flags": flags})
            print("Medcheck flags:", flags)
        reply = convo.send_reminder_and_record(user_id, ev)
        logger.info({"event": "reminder_interaction", "user": user_id, "event": ev, "reply": reply})
        print("Conversation reply:", reply)

    # Doctor mode demo
    print("\nDoctor mode demo: retrieving patient memory and adding advice.")
    patient_history = memory.get_user_memory(user_id)
    print("Patient memory snapshot:", json.dumps(patient_history, indent=2)[:1000])
    doctor_note = "Recommend follow-up with cardiology for lipid management. Consider lipid panel and liver enzymes."
    convo.doctor_add_advice(user_id, doctor_id="dr-1", advice_text=doctor_note, related_specialties=["Cardiology", "Clinical Pathology"])
    print("Doctor advice added to memory. Check memory file.")

    print("Demo complete. Check logs/ and memory/ for outputs.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="Run demo")
    args = parser.parse_args()
    if args.demo:
        root = os.path.dirname(os.path.dirname(__file__))
        os.makedirs(os.path.join(root, "logs"), exist_ok=True)
        os.makedirs(os.path.join(root, "memory"), exist_ok=True)
        demo()
