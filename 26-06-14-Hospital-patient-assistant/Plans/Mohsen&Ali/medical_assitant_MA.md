# Agentic Medical System Architecture

## Project Overview

An agentic medical system that assists patients through:

1. Multi-modal interaction (Text, Voice, Images, Phone Calls)
2. Appointment scheduling
3. Initial diagnosis and triage
4. Emergency response management
5. Loyalty and feedback management
6. Human-in-the-loop escalation for uncertain cases

---

# High-Level Architecture

```text
                           ┌──────────────────────┐
                           │      Patient         │
                           └──────────┬───────────┘
                                      │
             ┌────────────────────────┼────────────────────────┐
             │                        │                        │
             ▼                        ▼                        ▼
      Text Chat                Voice Input              Phone Call
                                                     (Call Agent)

                                      │
                                      ▼
                    ┌─────────────────────────────────┐
                    │        Orchestrator Agent       │
                    │                                 │
                    │ - Authentication                │
                    │ - Session Management            │
                    │ - Routing Decisions             │
                    └──────────────┬──────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
         Scheduling Request             Medical Complaint
                    │                             │
                    ▼                             ▼
         ┌──────────────────┐       ┌────────────────────────┐
         │ Scheduling Agent │       │    Diagnosis Agent     │
         └────────┬─────────┘       └───────────┬────────────┘
                  │                             │
                  ▼                             ▼
       Doctor Availability DB        Medical Knowledge Base
                                     (Vector Database + RAG)

                  │                             │
                  ▼                             ▼
      Available? Yes / No            Diagnosis Success?
                  │                             │
          ┌───────┴────────┐          ┌─────────┴─────────┐
          │                │          │                   │
          ▼                ▼          ▼                   ▼
     Available         Not Available Success          Failed
          │                │          │                   │
          ▼                ▼          ▼                   ▼
  Booking Confirmation  Suggest  Classify Case      Human Doctor
                         Another      │             (HITL)
                        Hospital       │
                                      ▼
                           ┌──────────────────┐
                           │ Urgent ?         │
                           └──────┬───────────┘
                                  │
                      ┌───────────┴───────────┐
                      │                       │
                      ▼                       ▼
               Non-Urgent                 Urgent
                      │                       │
                      ▼                       ▼
              Scheduling Agent      Emergency Agent
                                              │
                         ┌────────────────────┴──────────────────┐
                         │                                       │
                         ▼                                       ▼
            Frequent Ambulance User?                    First-Time User
                         │                                       │
                  ┌──────┴──────┐                         Set Timer
                  │             │                         Based On
                  ▼             ▼                         Diagnosis
            Yes (Direct)       No                              │
                  │             │                              ▼
                  ▼             └────────────────────► Ambulance Dispatch
          Ambulance Dispatch

```

---

# Detailed Workflow

## 1. Authentication

Patient logs in through:

* Web Chat
* Mobile App
* Voice Assistant
* Phone Call

The orchestrator checks:

* Patient Profile
* Medical History
* Previous Diagnoses
* Previous Ambulance Requests
* Loyalty Points

---

## 2. Scheduling Flow

### Request

Patient requests:

* Doctor Appointment
* Department Appointment

### Scheduling Agent

Queries:

* Doctor Database
* Available Clinics
* Department Availability

### Available Appointment

1. Present available slots.
2. Patient selects slot.
3. Appointment stored.
4. Loyalty points added.
5. Feedback workflow scheduled.

### No Available Appointment

Recommend:

* Emergency Department
* Another Hospital
* Nearest Available Clinic

---

## 3. Diagnosis Flow

### Inputs

Patient may provide:

* Text Complaint
* Voice Complaint
* Medical Image
* Combined Inputs

### Diagnosis Agent

Uses:

* Multimodal LLM
* Medical RAG
* Vector Database

Output:

* Department Classification
* Confidence Score
* Urgency Score

Examples:

| Symptom         | Classification |
| --------------- | -------------- |
| Chest Pain      | Cardiology     |
| Eye Redness     | Ophthalmology  |
| Bone Fracture   | Orthopedics    |
| Severe Headache | Neurology      |

---

## 4. Non-Urgent Cases

Diagnosis Agent → Scheduling Agent

Flow:

Diagnosis → Department → Appointment Booking

Example:

Eye infection detected.

Diagnosis Agent:
"Ophthalmology"

↓

Scheduling Agent:
Find ophthalmologist appointment.

---

## 5. Urgent Cases

Diagnosis Agent identifies:

* Heart Attack
* Stroke
* Severe Trauma
* Internal Bleeding
* Respiratory Failure

### Emergency Agent

Determines:

* Severity
* Ambulance Requirement
* Dispatch Timing

### Existing High-Risk Patient

If patient history shows:

* Frequent ambulance requests
* Chronic heart disease
* High-risk status

Immediately dispatch ambulance.

### New Patient

Set emergency timer according to diagnosis.

Examples:

| Condition     | Timer     |
| ------------- | --------- |
| Heart Attack  | 30 sec    |
| Stroke        | 60 sec    |
| Severe Trauma | Immediate |

After timeout:

Ambulance dispatched automatically.

---

## 6. Human-in-the-Loop Flow

Triggered when:

* Low confidence diagnosis
* Conflicting symptoms
* Insufficient information
* Unknown disease pattern

### Workflow

Diagnosis Agent generates:

* Patient Summary
* Medical History Summary
* Symptoms Report
* Suggested Department

↓

Emergency Doctor reviews case.

↓

Doctor contacts patient directly.

---

## 7. Loyalty System

After appointment booking:

Loyalty Tool:

* Add Points
* Update Patient Profile
* Generate Offers

Example:

| Points | Benefit           |
| ------ | ----------------- |
| 100    | 5% Discount       |
| 300    | 10% Discount      |
| 500    | Free Consultation |

---

## 8. Feedback Agent

Cron Job:

Runs 24 hours after appointment.

Workflow:

1. Contact patient.
2. Collect satisfaction score.
3. Collect health status.
4. Store feedback.

Stored in:

* R&D Database
* Analytics Database

Used for:

* Service Improvement
* Model Fine-Tuning
* KPI Tracking

---

# Recommended Tech Stack

## Frontend

* Next.js
* React
* Tailwind CSS

## Backend

* FastAPI
* Python

## Agent Framework

* PydanticAI
* OpenAI Agents SDK
* LangGraph (optional)

## LLMs

### Cloud

* GPT-5
* Claude Sonnet

### Local

* Qwen3
* Llama 4
* Gemma 3

## Multimodal Models

* Qwen2.5-VL
* Llama Vision
* GPT-4o

## Speech-to-Text

* Whisper Large V3
* Parakeet

## Text-to-Speech

* Kokoro TTS
* Chatterbox TTS

## Vector Database

* Qdrant

## Relational Database

* PostgreSQL

## Cache

* Redis

## Task Scheduling

* Celery
* Redis Queue
* Cron Jobs

## Monitoring

* Langfuse
* OpenTelemetry

---

# Suggested Repository Structure

```text
medical-agentic-system/
│
├── frontend/
│
├── backend/
│   ├── agents/
│   │   ├── orchestrator/
│   │   ├── diagnosis/
│   │   ├── scheduling/
│   │   ├── emergency/
│   │   ├── feedback/
│   │   └── loyalty/
│   │
│   ├── rag/
│   │   ├── ingestion/
│   │   ├── retrieval/
│   │   └── vectorstore/
│   │
│   ├── database/
│   │   ├── patient_db/
│   │   ├── doctor_db/
│   │   └── analytics_db/
│   │
│   ├── api/
│   ├── tools/
│   ├── workflows/
│   └── services/
│
├── docs/
│
├── infrastructure/
│
├── tests/
│
└── deployment/
```

---

# MVP Development Order

Phase 1:

* Authentication
* Orchestrator Agent
* Patient Database

Phase 2:

* Scheduling Agent
* Doctor Database

Phase 3:

* Medical RAG
* Diagnosis Agent

Phase 4:

* Emergency Agent

Phase 5:

* Loyalty System

Phase 6:

* Feedback Agent

Phase 7:

* Voice Calls
* Phone Agent

Phase 8:

* Monitoring
* Analytics
* Production Deployment

```
```
