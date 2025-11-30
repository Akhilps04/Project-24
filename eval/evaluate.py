# eval/evaluate.py
"""
Evaluation skeleton: unit tests + human eval CSV template.
Run: python eval/evaluate.py
"""

import csv
import os
from pathlib import Path

def run_unit_tests():
    print("Running unit tests (basic)...")
    from tools.medcheck_tool import medcheck
    sample = [{"name":"A","time":"08:00"},{"name":"B","time":"08:00"}]
    assert medcheck(sample), "medcheck failed to flag conflict"
    print("Unit tests passed.")

def create_human_eval_template():
    Path("eval").mkdir(exist_ok=True)
    out = Path("eval/human_eval.csv")
    if out.exists():
        print("human_eval.csv already exists at eval/human_eval.csv")
        return
    rows = [
        ["sample_id","prompt","agent_output","rater","clarity(1-5)","helpfulness(1-5)","notes"],
        ["1","Did I take my morning meds?","Please confirm whether you took Atorvastatin 10mg","rater1",4,4,"sample"]
    ]
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerows(rows)
    print("Created eval/human_eval.csv template.")

if __name__ == "__main__":
    run_unit_tests()
    create_human_eval_template()
    print("Evaluation skeleton ready.")
