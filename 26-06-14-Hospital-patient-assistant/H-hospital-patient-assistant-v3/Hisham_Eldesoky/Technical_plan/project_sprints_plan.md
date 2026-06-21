# Hospital Patient Assistant v3 — Modules & Sprints Plan

**Stack decisions locked in:**
- 🐳 **Docker** — All services run via `docker-compose` (PostgreSQL, Redis, Qdrant, FastAPI)
- 🤖 **OpenAI API first** — `openai` Python SDK for all LLM calls

---

## Full Project Folder Structure

```
H-hospital-patient-assistant-v3/
│
├── backend/                        ← FastAPI Python backend
│   ├── app/
│   │   ├── main.py                 ← FastAPI app entry point
│   │   ├── config.py               ← All settings (reads from .env)
│   │   ├── database.py             ← PostgreSQL connection (SQLAlchemy)
│   │   │
│   │   ├── models/                 ← Database table definitions (ORM)
│   │   │   ├── patient.py
│   │   │   ├── doctor.py
│   │   │   ├── appointment.py
│   │   │   └── audit_log.py
│   │   │
│   │   ├── schemas/                ← Pydantic input/output shapes (validation)
│   │   │   ├── patient.py
│   │   │   ├── scheduling.py
│   │   │   ├── symptom.py
│   │   │   └── diagnosis.py
│   │   │
│   │   ├── api/                    ← HTTP route handlers
│   │   │   └── v1/
│   │   │       ├── auth.py         ← Login / session endpoints
│   │   │       ├── scheduling.py   ← Book / reschedule endpoints
│   │   │       ├── medical.py      ← Symptom + diagnosis endpoints
│   │   │       └── emergency.py    ← Emergency trigger endpoint
│   │   │
│   │   ├── agents/                 ← All agent logic lives here
│   │   │   ├── orchestrator.py
│   │   │   ├── scheduling_agent.py
│   │   │   ├── symptom_intake.py
│   │   │   ├── triage_engine.py    ← Rule-based only, NO LLM
│   │   │   ├── diagnosis_agent.py
│   │   │   ├── safety_check.py
│   │   │   ├── emergency_agent.py
│   │   │   ├── loyalty_agent.py
│   │   │   └── feedback_agent.py
│   │   │
│   │   ├── rag/                    ← Medical document search (Qdrant)
│   │   │   ├── vector_store.py     ← Connect to Qdrant
│   │   │   └── retriever.py        ← Search medical guidelines
│   │   │
│   │   ├── tasks/                  ← Background jobs (Celery)
│   │   │   ├── loyalty_task.py
│   │   │   └── feedback_task.py
│   │   │
│   │   └── core/                   ← Shared utilities
│   │       ├── auth.py             ← JWT token logic
│   │       ├── audit.py            ← Write to audit log
│   │       └── exceptions.py       ← Custom error types
│   │
│   ├── migrations/                 ← Alembic DB migrations
│   ├── tests/                      ← Unit & integration tests
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/                       ← Next.js patient-facing UI
│   ├── app/
│   │   ├── page.tsx                ← Home / patient chat page
│   │   ├── appointments/
│   │   │   └── page.tsx            ← View booked appointments
│   │   └── clinician/
│   │       └── page.tsx            ← HITL clinician review dashboard
│   ├── components/
│   │   ├── ChatWindow.tsx
│   │   ├── SymptomForm.tsx
│   │   └── AppointmentCard.tsx
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml              ← Runs ALL services locally with one command
└── README.md
```

---

## Module 0: Docker Environment Setup (Do This First!)
**Goal:** Get all infrastructure running locally before writing any application code.

### Sprint 0.1 — Write docker-compose.yml
**Files to create:**
- `docker-compose.yml`
- `backend/.env.example`
- `backend/Dockerfile`

**docker-compose.yml:**
```yaml
version: "3.9"
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: hospital
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: hospital_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file: ./backend/.env
    depends_on:
      - db
      - redis
      - qdrant
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  postgres_data:
  qdrant_data:
```

**backend/Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
```

**backend/.env.example:**
```
DATABASE_URL=postgresql://hospital:secret@db:5432/hospital_db
REDIS_URL=redis://redis:6379/0
QDRANT_URL=http://qdrant:6333
OPENAI_API_KEY=sk-your-key-here
SECRET_KEY=your-jwt-secret-here
```

**Start everything with one command:**
```bash
docker-compose up --build
```

**Verification:** Visit `http://localhost:8000/docs` — you should see the FastAPI docs page.

---

## Module 1: Core Infrastructure & Orchestration (MVP Phase 1)

### Sprint 1.1 — FastAPI Setup & Patient Database
**Files to create:**
- `backend/requirements.txt`
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/database.py`
- `backend/app/models/patient.py`

**backend/requirements.txt:**
```
fastapi==0.111.0
uvicorn==0.30.0
sqlalchemy==2.0.30
psycopg2-binary==2.9.9
alembic==1.13.1
pydantic-settings==2.2.1
openai==1.30.0
qdrant-client==1.9.1
celery==5.4.0
redis==5.0.4
python-jose==3.3.0
python-multipart==0.0.9
```

**backend/app/config.py:**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    QDRANT_URL: str
    OPENAI_API_KEY: str
    SECRET_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()
```

**backend/app/models/patient.py:**
```python
from sqlalchemy import Column, String, Date, Integer
from app.database import Base

class Patient(Base):
    __tablename__ = "patients"
    id           = Column(String, primary_key=True)   # e.g. "p-001"
    name         = Column(String, nullable=False)
    dob          = Column(Date)
    allergies    = Column(String, default="")          # "NSAIDs,penicillin"
    medications  = Column(String, default="")          # "metformin,aspirin"
    loyalty_pts  = Column(Integer, default=0)
```

**Input (POST /api/v1/patients):**
```json
{"name": "Ahmed Ali", "dob": "1990-05-10", "allergies": "NSAIDs"}
```
**Output:**
```json
{"patient_id": "p-001", "status": "created"}
```

---

### Sprint 1.2 — Orchestrator Agent
**Files to create:**
- `backend/app/agents/orchestrator.py`
- `backend/app/api/v1/auth.py`
- `backend/app/schemas/patient.py`
- `backend/app/core/auth.py`

**backend/app/agents/orchestrator.py:**
```python
from openai import OpenAI
from app.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def classify_intent(message: str) -> str:
    """Returns 'scheduling' or 'medical_complaint'"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",           # fast + cheap for routing only
        temperature=0,
        messages=[
            {"role": "system", "content":
             "Classify the patient's message as exactly one of: "
             "'scheduling' or 'medical_complaint'. Reply with only that word."},
            {"role": "user", "content": message}
        ]
    )
    return response.choices[0].message.content.strip()
```

**Input (POST /api/v1/chat):**
```json
{"patient_id": "p-001", "raw_message": "I want to see a cardiologist"}
```
**Output:**
```json
{"request_type": "scheduling", "routed_to": "Scheduling_Agent", "session_id": "s-abc123"}
```

---

## Module 2: Scheduling System (MVP Phase 2)

### Sprint 2.1 — Doctor Availability Database
**Files to create:**
- `backend/app/models/doctor.py`
- `backend/app/models/appointment.py`

**backend/app/models/doctor.py:**
```python
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from app.database import Base

class Doctor(Base):
    __tablename__ = "doctors"
    id         = Column(String, primary_key=True)
    name       = Column(String)
    department = Column(String)   # e.g. "Cardiology", "Pulmonology"

class TimeSlot(Base):
    __tablename__ = "time_slots"
    id         = Column(String, primary_key=True)
    doctor_id  = Column(String, ForeignKey("doctors.id"))
    datetime   = Column(DateTime)
    is_booked  = Column(Boolean, default=False)
```

**Input (GET /api/v1/slots?department=Cardiology&date=2026-10-12):**
```json
{"department": "Cardiology", "date": "2026-10-12"}
```
**Output:**
```json
[{"slot_id": "sl-1", "time": "10:00 AM", "doctor": "Dr. Samira Hassan"}]
```

---

### Sprint 2.2 — Scheduling Agent
**Files to create:**
- `backend/app/agents/scheduling_agent.py`
- `backend/app/api/v1/scheduling.py`
- `backend/app/schemas/scheduling.py`

**backend/app/agents/scheduling_agent.py:**
```python
from openai import OpenAI
import json
from app.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Tools the LLM can call
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_slots",
            "description": "Search available appointment slots by department and date",
            "parameters": {
                "type": "object",
                "properties": {
                    "department": {"type": "string"},
                    "date": {"type": "string", "description": "YYYY-MM-DD"}
                },
                "required": ["department", "date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_slot",
            "description": "Book a specific appointment slot for a patient",
            "parameters": {
                "type": "object",
                "properties": {
                    "slot_id": {"type": "string"},
                    "patient_id": {"type": "string"}
                },
                "required": ["slot_id", "patient_id"]
            }
        }
    }
]

def run(patient_id: str, request_text: str) -> dict:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a hospital scheduling assistant."},
            {"role": "user", "content": request_text}
        ],
        tools=tools,
        tool_choice="auto"
    )
    # Handle tool calls here (search DB, then book)
    return {"status": "confirmed", "appointment_id": "a-899"}
```

**Input (POST /api/v1/schedule):**
```json
{"patient_id": "p-001", "request_text": "Book Dr. Samira on Tuesday at 10 AM"}
```
**Output:**
```json
{"appointment_id": "a-899", "doctor": "Dr. Samira", "time": "2026-10-14 10:00", "status": "confirmed"}
```

---

## Module 3: Triage & Symptom Intake (MVP Phase 3)

### Sprint 3.1 — Symptom Intake Agent
**Files to create:**
- `backend/app/agents/symptom_intake.py`
- `backend/app/api/v1/medical.py`
- `backend/app/schemas/symptom.py`

**backend/app/agents/symptom_intake.py:**
```python
from openai import OpenAI
import json
from app.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_PROMPT = """
You are a medical intake assistant. Extract symptoms from the patient's message and return ONLY valid JSON.
Format:
{
  "symptoms": [
    {"name": "string", "location": "string", "duration": "string", "severity": "low|medium|high"}
  ]
}
"""

def extract_symptoms(complaint_text: str) -> dict:
    response = client.chat.completions.create(
        model="gpt-4o",           # vision-capable for future image support
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": complaint_text}
        ]
    )
    return json.loads(response.choices[0].message.content)
```

**Input (POST /api/v1/medical/symptoms):**
```json
{"patient_id": "p-001", "complaint_text": "My chest has been hurting terribly for 30 minutes"}
```
**Output:**
```json
{"symptoms": [{"name": "chest pain", "location": "chest", "duration": "30 mins", "severity": "high"}]}
```

---

### Sprint 3.2 — Triage Engine (Rule-Based, NO LLM)
**Files to create:**
- `backend/app/agents/triage_engine.py`

**backend/app/agents/triage_engine.py:**
```python
# ⚠️ CRITICAL: This file must never import openai or call any LLM.
# It must be 100% deterministic for medical safety.

ESI_1_KEYWORDS = [
    "chest pain", "heart attack", "stroke", "not breathing",
    "unconscious", "severe bleeding", "anaphylaxis", "seizure"
]
ESI_2_KEYWORDS = [
    "high fever", "severe headache", "difficulty breathing",
    "severe abdominal pain", "broken bone"
]
ESI_3_KEYWORDS = [
    "moderate pain", "vomiting", "dizziness", "mild fever"
]

def score(symptoms: list[dict]) -> dict:
    """Returns ESI urgency level 1 (life-threat) to 5 (non-urgent)."""
    symptom_names = " ".join([s["name"].lower() for s in symptoms])

    for kw in ESI_1_KEYWORDS:
        if kw in symptom_names:
            return {"urgency_level": 1, "status": "Life-threat", "triggered_by": kw}

    for kw in ESI_2_KEYWORDS:
        if kw in symptom_names:
            return {"urgency_level": 2, "status": "Urgent", "triggered_by": kw}

    for kw in ESI_3_KEYWORDS:
        if kw in symptom_names:
            return {"urgency_level": 3, "status": "Less-urgent", "triggered_by": kw}

    return {"urgency_level": 4, "status": "Non-urgent", "triggered_by": None}
```

**Input:**
```json
{"symptoms": [{"name": "chest pain", "severity": "high"}]}
```
**Output:**
```json
{"urgency_level": 1, "status": "Life-threat", "triggered_by": "chest pain"}
```

---

## Module 4: Clinical Reasoning & Safety (MVP Phase 4)

### Sprint 4.1 — Diagnosis Reasoning Agent + Medical RAG
**Files to create:**
- `backend/app/rag/vector_store.py`
- `backend/app/rag/retriever.py`
- `backend/app/agents/diagnosis_agent.py`
- `backend/app/schemas/diagnosis.py`

**backend/app/rag/retriever.py:**
```python
from qdrant_client import QdrantClient
from openai import OpenAI
from app.config import settings

qdrant = QdrantClient(url=settings.QDRANT_URL)
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

def embed(text: str) -> list[float]:
    """Convert text to a vector using OpenAI embeddings."""
    response = openai_client.embeddings.create(
        model="text-embedding-3-small", input=text
    )
    return response.data[0].embedding

def retrieve_medical_context(symptoms: list[dict], top_k: int = 5) -> list[str]:
    query = " ".join([s["name"] for s in symptoms])
    vector = embed(query)
    results = qdrant.search(
        collection_name="medical_guidelines",
        query_vector=vector,
        limit=top_k
    )
    return [r.payload["text"] for r in results]
```

**backend/app/agents/diagnosis_agent.py:**
```python
from openai import OpenAI
import json
from app.config import settings
from app.rag.retriever import retrieve_medical_context

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def diagnose(symptoms: list, emr_history: str) -> dict:
    rag_context = retrieve_medical_context(symptoms)
    context_text = "\n".join(rag_context)

    response = client.chat.completions.create(
        model="gpt-4o",           # Use strongest model here — this is highest risk
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content":
             "You are a clinical reasoning assistant. Based on symptoms, patient history, "
             "and medical guidelines, suggest the most appropriate hospital department. "
             "Return JSON: {candidate_department, confidence, reasoning, cited_sources[]}"},
            {"role": "user", "content":
             f"Symptoms: {symptoms}\n\nPatient history: {emr_history}\n\nGuidelines:\n{context_text}"}
        ]
    )
    return json.loads(response.choices[0].message.content)
```

**Input (POST /api/v1/medical/diagnose):**
```json
{"symptoms": [{"name": "fever"}, {"name": "cough"}], "patient_id": "p-001"}
```
**Output:**
```json
{
  "candidate_department": "Pulmonology",
  "confidence": 0.87,
  "reasoning": "Fever + cough with asthma history suggests respiratory issue.",
  "cited_sources": ["WHO Asthma Guidelines 2024"]
}
```

---

### Sprint 4.2 — Clinical Safety Check Gate
**Files to create:**
- `backend/app/agents/safety_check.py`

**backend/app/agents/safety_check.py:**
```python
# ⚠️ CRITICAL: This is a hard gate. No LLM is used for the actual pass/fail decision.
# The LLM only generates a human-readable explanation if needed.

CONTRAINDICATION_DB = {
    "ibuprofen":   ["nsaids", "aspirin allergy"],
    "aspirin":     ["nsaids", "aspirin allergy"],
    "penicillin":  ["penicillin allergy"],
    "amoxicillin": ["penicillin allergy"],
    "codeine":     ["opioid allergy"],
}

def check_safety(draft_text: str, patient_allergies: list[str]) -> dict:
    """
    Checks if any drug mentioned in the draft output conflicts
    with the patient's known allergies.
    """
    flags = []
    lower_draft = draft_text.lower()
    lower_allergies = [a.lower() for a in patient_allergies]

    for drug, conflicts in CONTRAINDICATION_DB.items():
        if drug in lower_draft:
            for allergy in lower_allergies:
                if allergy in conflicts:
                    flags.append(f"⚠️ {drug} conflicts with patient allergy: {allergy}")

    return {
        "pass_fail": "Fail" if flags else "Pass",
        "contraindication_flags": flags,
        "grounding_note": "Manual contraindication check passed" if not flags else "Requires HITL review"
    }
```

**Input:**
```json
{"draft_text": "Consider Ibuprofen for pain relief.", "patient_allergies": ["NSAIDs"]}
```
**Output (Fail):**
```json
{
  "pass_fail": "Fail",
  "contraindication_flags": ["⚠️ ibuprofen conflicts with patient allergy: nsaids"],
  "grounding_note": "Requires HITL review"
}
```
**Output (Pass):**
```json
{
  "pass_fail": "Pass",
  "contraindication_flags": [],
  "grounding_note": "Manual contraindication check passed"
}
```

---

## Module 5: Emergency & Automation (MVP Phases 5, 6, 7)

### Sprint 5.1 — Emergency Agent + Audit Log
**Files to create:**
- `backend/app/agents/emergency_agent.py`
- `backend/app/models/audit_log.py`
- `backend/app/core/audit.py`
- `backend/app/api/v1/emergency.py`

**backend/app/agents/emergency_agent.py:**
```python
import asyncio
from openai import OpenAI
from app.config import settings
from app.core.audit import write_audit_log

client = OpenAI(api_key=settings.OPENAI_API_KEY)

async def notify_clinician(patient_id: str):
    """Always fires IMMEDIATELY — parallel to everything else."""
    print(f"[ALERT] On-call clinician notified for patient {patient_id}")
    # In production: send SMS/push notification via Twilio or Firebase

async def dispatch_ambulance(patient_id: str):
    print(f"[DISPATCH] Ambulance dispatched for patient {patient_id}")
    # In production: call hospital EMS API
    write_audit_log(event="ambulance_dispatched", patient_id=patient_id)

async def timed_dispatch(patient_id: str, seconds: int = 60):
    await asyncio.sleep(seconds)
    await dispatch_ambulance(patient_id)

async def handle_emergency(patient_id: str, known_high_risk: bool) -> dict:
    # Step 1: ALWAYS alert clinician in parallel immediately
    asyncio.create_task(notify_clinician(patient_id))

    # Step 2: Dispatch decision based on risk
    if known_high_risk:
        await dispatch_ambulance(patient_id)
        return {"dispatch": "immediate", "clinician_alerted": True}
    else:
        asyncio.create_task(timed_dispatch(patient_id, seconds=60))
        return {"dispatch": "timed", "timer_seconds": 60, "clinician_alerted": True}
```

**Input (POST /api/v1/emergency):**
```json
{"patient_id": "p-001", "urgency_level": 1, "known_high_risk": false}
```
**Output:**
```json
{"dispatch": "timed", "timer_seconds": 60, "clinician_alerted": true}
```

---

### Sprint 5.2 — Background Agents (Loyalty & Feedback)
**Files to create:**
- `backend/app/tasks/loyalty_task.py`
- `backend/app/tasks/feedback_task.py`
- `backend/app/agents/loyalty_agent.py`
- `backend/app/agents/feedback_agent.py`

**backend/app/tasks/loyalty_task.py:**
```python
from celery import Celery
from app.config import settings

celery_app = Celery("tasks", broker=settings.REDIS_URL)

@celery_app.task
def award_loyalty_points(patient_id: str, points: int = 50):
    """Fires immediately after booking — non-blocking."""
    # db update: patient.loyalty_pts += points
    print(f"Awarded {points} points to patient {patient_id}")
    return {"patient_id": patient_id, "points_added": points}
```

**backend/app/tasks/feedback_task.py:**
```python
@celery_app.task
def send_feedback_request(patient_id: str, appointment_id: str):
    """Called with countdown=86400 so it fires 24 hours after booking."""
    message = "How was your visit? Are you feeling better? Reply 1-5."
    # send_sms(patient_id, message)
    print(f"Feedback sent to {patient_id} for appointment {appointment_id}")
```

**How to trigger after a booking (in scheduling_agent.py):**
```python
# After booking confirmed:
award_loyalty_points.delay(patient_id=patient_id, points=50)
send_feedback_request.apply_async(
    kwargs={"patient_id": patient_id, "appointment_id": appointment_id},
    countdown=86400   # 24 hours in seconds
)
```

**Input (triggered internally on booking):**
```json
{"event": "booking_completed", "patient_id": "p-001", "appointment_id": "a-899"}
```
**Output (Loyalty):**
```json
{"patient_id": "p-001", "points_added": 50, "new_balance": 150}
```

---

## Build Order Summary

| Sprint | What you build | Key files |
|--------|---------------|-----------|
| 0.1 | Docker environment | `docker-compose.yml`, `Dockerfile`, `.env` |
| 1.1 | FastAPI + Patient DB | `main.py`, `database.py`, `models/patient.py` |
| 1.2 | Orchestrator routing | `agents/orchestrator.py`, `api/v1/auth.py` |
| 2.1 | Doctor DB schema | `models/doctor.py`, `models/appointment.py` |
| 2.2 | Scheduling agent | `agents/scheduling_agent.py` |
| 3.1 | Symptom intake | `agents/symptom_intake.py` |
| 3.2 | Triage rules engine | `agents/triage_engine.py` |
| 4.1 | Diagnosis + RAG | `agents/diagnosis_agent.py`, `rag/retriever.py` |
| 4.2 | Safety check gate | `agents/safety_check.py` |
| 5.1 | Emergency agent | `agents/emergency_agent.py`, `core/audit.py` |
| 5.2 | Background workers | `tasks/loyalty_task.py`, `tasks/feedback_task.py` |

---

## Quick Start Commands

```bash
# 1. Copy env template and fill in your OpenAI API key
cp backend/.env.example backend/.env

# 2. Start all services (PostgreSQL, Redis, Qdrant, FastAPI)
docker-compose up --build

# 3. Open API docs
# http://localhost:8000/docs

# 4. Run tests
docker-compose exec backend pytest tests/ -v
```
