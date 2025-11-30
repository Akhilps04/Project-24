# list_models.py
import os, requests, json
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
ENDPOINT = os.getenv("GEMINI_ENDPOINT", "https://generativelanguage.googleapis.com/v1beta/models")

if not API_KEY:
    print("No GEMINI_API_KEY in .env")
    raise SystemExit(1)

url = f"{ENDPOINT}?key={API_KEY}"
print("Calling ListModels:", url)
r = requests.get(url, timeout=15)
print("HTTP", r.status_code)
try:
    data = r.json()
    print(json.dumps(data, indent=2)[:4000])  # print first chunk
    # If there is a 'models' list, print names
    if isinstance(data, dict):
        for k in ("models","model","availableModels"):
            if k in data and isinstance(data[k], list):
                print("\nModel names:")
                for m in data[k]:
                    if isinstance(m, dict) and "name" in m:
                        print(" -", m["name"])
                break
except Exception as e:
    print("Failed to parse response:", e)
    print("Raw body:", r.text[:2000])
