# 🩺 **Medication Buddy: A Memory-Aware Healthcare Agent**

Medication Buddy is an AI-powered personal health assistant that helps users manage medications, understand prescriptions, track adherence, and receive simple doctor guidance.
The system uses **memory-first reasoning**, **multi-agent utility tools**, and **Gemini models** to simulate an intelligent, safe healthcare assistant.

This project was built as part of the Gemini Agents Capstone.

---

# 📌 **Problem Statement**

Managing multiple medications, prescriptions, reminders, and doctor instructions is difficult for many people.
Patients often forget:

* When they took a medication
* What the medication is for
* Whether there are timing conflicts
* What the doctor advised last visit
* What their prescription says
* Which specialist they should consult
* How to interpret medical documents

This leads to missed doses, dangerous self-interpretation, and confusion.

**Users need a simple assistant that remembers their medical context, retrieves past events instantly, interprets documents safely, and interacts naturally.**

---

# 🤖 **Why Agents?**

Agents are the right solution because they can:

### **1. Maintain long-term memory**

Unlike normal chat AI, the agent stores structured events (reminders, adherence logs, doctor advice, prescription summaries).
This allows it to answer questions like:

* “Did I take my Metformin today?”
* “What did the doctor tell me last time?”
* “What medicines were in that prescription I uploaded?”

### **2. Use tools**

The agent integrates multiple tools:

* **Docs Processor** → extract keywords from prescriptions
* **MedCheck Tool** → detect conflicts, timing mismatches
* **MemoryBank** → retrieve and summarize medical history
* **Logger** → audit all events

### **3. Use model calls only when needed**

The agent:

1. Checks memory
2. If relevant data is found, replies instantly using memory
3. Only falls back to Gemini when memory doesn't have the answer

This is efficient, explainable, and safe.

### **4. Allow doctor mode**

Doctors can add structured advice:

* “Monitor BP daily.”
* “Increase water intake.”
* “Take atorvastatin at night.”

This becomes part of the patient’s “medical timeline”.

---

# 🏗️ **Architecture Overview**

Here is the full project architecture:

```mermaid
flowchart LR
  subgraph Client
    CLI[CLI / Demo UI]
    Mobile[Mobile / Browser UI]
  end

  subgraph AgentLayer
    Agent[ConversationalAgent]
    Memory[MemoryBank (JSON)]
    Logger[JSON Logger]
    Medcheck[Medcheck Tool]
    DocProc[Docs Processor]
  end

  subgraph ModelLayer
    Gemini[Gemini API]
  end

  subgraph Storage
    Files[Local files / sample_data / logs/]
  end

  CLI --> Agent
  Mobile --> Agent

  Agent -->|search / read| Memory
  Agent -->|append events| Memory
  Agent --> Logger
  Agent --> Medcheck
  Agent --> DocProc
  Agent -->|call when needed| Gemini
  DocProc --> Memory
  Medcheck --> Agent
  Logger --> Files
  Memory --> Files
  Gemini -->|responses| Agent
```
<img width="1944" height="2027" alt="_- visual selection (2)" src="https://github.com/user-attachments/assets/2bcf2dbb-b845-4415-84d6-f2744cee0ce8" />

---
<img width="1729" height="1706" alt="_- visual selection (1)" src="https://github.com/user-attachments/assets/fa05913e-3b48-497e-9b52-5ff43c0d38ad" />
---
<img width="1902" height="1719" alt="_- visual selection" src="https://github.com/user-attachments/assets/cc9c8950-27a6-4abf-ba5f-8e605803cb47" />

---

# 🔧 **Features Implemented**

### ✔ Memory-first responder

Searches memory for keyword matches before calling Gemini.

### ✔ Medical adherence tracking

Stores:

* Time taken
* Medication name
* Doctor notes
* Frequency
* Timestamp

### ✔ Prescription upload handling

Extracts keywords like:

* “metformin 500mg twice daily”
* “atorvastatin 10mg nightly”

Maps them to specialties:

* Endocrinology
* Cardiology
* Primary Care

### ✔ Doctor mode

Doctors add structured advice:

```
doctor
Doctor id: dr-1
Advice: Monitor BP daily.
Specialties: Cardiology
```

### ✔ Medcheck tool integration

Checks for conflicts (simple rule-based).

### ✔ JSON logging

Every agent action is stored for debugging and transparency.

### ✔ Robust Gemini API integration

Avoids MAX_TOKENS truncation
Fallbacks when the API returns unexpected shapes.

---

# 🖥️ **Demo (CLI)**

### **1. Medication Reminder**

```
You: remind me to take Metformin
Let's set a reminder.
Medicine name: Metformin 500mg
Time: 08:00
Frequency: daily
```

The system replies:

```
It's time to take your Metformin 500mg at 08:00.
Have you taken it?
```

### **2. Memory query**

```
You: Did I take my Metformin today?
```

Response:

```
I found these saved notes related to your question:

- Took Metformin 500mg at 2025-11-28 08:01
```

### **3. Prescription upload**

```
You: doc
```

Response:

```
Extracted keywords:
- metformin 500mg
- atorvastatin 10mg

Suggested specialties:
- Primary Care
- Internal Medicine
```

### **4. Doctor mode**

```
You: doctor
Doctor id: dr-1
Advice: Increase water intake and monitor BP daily.
Specialties: Cardiology
```

### **5. Memory-first inference**

```
You: Should I check my BP today?
```

Response (memory-based):

```
Your doctor previously advised monitoring blood pressure.
```

---

# 🛠️ **The Build**

### **Languages & Tools**

* Python 3.9
* Gemini API (via REST)
* Mermaid (architecture diagrams)
* JSON-based MemoryBank
* CLI interface
* Rule-based MedCheck tool
* Regex-based docs processor

### **Key Concepts Implemented**

✔ Tool calling
✔ Memory management
✔ State persistence
✔ Multi-agent utilities
✔ LLM fallback logic
✔ Error handling and truncation recovery

---

# 📚 **Folder Structure**

```
medication-buddy/
│
├── agents/
│   ├── convo_agent.py
│   └── cli_chat.py
│
├── memory/
│   └── memory_bank.json
│
├── tools/
│   ├── medcheck_tool.py
│   └── docs_processor.py
│
├── logs/
│   └── logs.jsonl
│
└── sample_data/
    └── prescription_sample.pdf
```

---

# 🚀 **If I Had More Time…**

I would extend the project into a full clinical assistant:

### 🔹 1. Include a scheduling engine

Actual timed reminders instead of simulated ones.

### 🔹 2. Build a mobile UI

With charts, reminders, pillbox visualization.

### 🔹 3. Add OCR for real prescription images

Using Gemini Vision.

### 🔹 4. Add drug–drug interaction databases

For real alerts.

### 🔹 5. Add per-user secure authentication

So the system can serve many users.

### 🔹 6. Deploy to Cloud Run or Agent Engine

To make it a real service available via API / web.

---

# 🎉  Thank you kaggle and Google for giving this opportunity
