# Agentic Medical System Architecture

## Project Overview

An agentic medical system that assists patients through:

1. Multi-modal interaction (Text, Audio Recorded, Images)
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

- Web Chat
- Voice Assistant
- Phone Call

The orchestrator checks:

- Patient Profile
- Medical History
- Previous Diagnoses
- Previous Ambulance Requests
- Loyalty Points

---

## 2. Scheduling Flow

### Request

Patient requests:

- Doctor Appointment
- Department Appointment

### Scheduling Agent

Queries:

- Doctor Database
- Available Clinics
- Department Availability

### Available Appointment

1. Present available slots.
2. Patient selects slot.
3. Appointment stored.
4. Loyalty points added.
5. Feedback workflow scheduled.

### No Available Appointment

Recommend:

- Emergency Department
- Another Hospital
- Nearest Available Clinic

---

## 3. Diagnosis Flow

### Inputs

Patient may provide:

- Text Complaint
- Voice Complaint
- Medical Image
- Combined Inputs

### Diagnosis Agent

Uses:

- Multimodal LLM
- Medical RAG
- Vector Database

Output:

- Department Classification
- Confidence Score
- Urgency Score

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

- Heart Attack
- Stroke
- Severe Trauma
- Internal Bleeding
- Respiratory Failure

### Emergency Agent

Determines:

- Severity
- Ambulance Requirement
- Emergency Alert Priority

### Existing High-Risk Patient

If patient history shows:

- Frequent ambulance requests
- Chronic heart disease
- High-risk status

Immediately generate emergency alert and notify hospital staff.

### New Patient

Set emergency timer according to diagnosis.

### Emergency Actions

- Generate Emergency Alert
- Notify Hospital Staff
- Recommend Ambulance Dispatch

Examples:

| Condition     | Timer     |
| ------------- | --------- |
| Heart Attack  | 30 sec    |
| Stroke        | 60 sec    |
| Severe Trauma | Immediate |

After timeout:

Emergency alert is generated and hospital staff are notified.

---

## 6. Human-in-the-Loop Flow

Triggered when:

- Low confidence diagnosis
- Conflicting symptoms
- Insufficient information
- Unknown disease pattern

### Workflow

Diagnosis Agent generates:

- Patient Summary
- Medical History Summary
- Symptoms Report
- Suggested Department

↓

Emergency Doctor reviews case.

↓

Doctor contacts patient directly.

---

## 7. Loyalty System

during appointment booking:
our scheduling agent check if patient have enough points to give him offer
make orchestrator agent tell user we have available slot and tell him
"u have [number] points you can use them to get [offer]"

if user tell u he want to use points apply the offer to the payment methode

after appointment booking:

Loyalty Tool:

- Add Points
- Update Patient Profile

Example:

| Points | Benefit           |
| ------ | ----------------- |
| 100    | 5% Discount       |
| 300    | 10% Discount      |
| 500    | Free Consultation |

---

# 8. Medication Reminders

## Purpose

After a patient finishes a doctor consultation and receives a prescription, the system automatically schedules medication reminders.

The goal is to improve medication adherence by notifying patients before their medication time.

---

## Workflow

Doctor Consultation

↓

Prescription Stored in Database

↓

Reminder Scheduler

(Cron Job)

↓

Telegram Notification

↓

Patient Receives Reminder

---

## Prescription Storage

Each prescription contains:

- Medication Name
- Dosage
- Frequency
- Start Date
- End Date
- Medication Times

Example:

- Augmentin
- 1 Tablet
- Every 12 Hours
- 08:00 AM
- 08:00 PM

---

## Reminder Scheduling

A scheduled job runs periodically and checks upcoming medication times.

Rule:

- Send reminder 30 minutes before medication time.

Example:

Medication Time:

08:00 AM

Reminder Sent:

07:30 AM

Telegram Message:

"Reminder: You should take Augmentin at 08:00 AM."

---

## Notification Channel

For the MVP, reminders are sent using Telegram Bot.

Benefits:

- Free
- Official API
- Easy Integration
- No Meta approval required
- Suitable for graduation projects

---

## Required Components

### Prescription Database

Stores:

- Patient Prescriptions
- Medication Schedule
- Treatment Duration

### Reminder Scheduler

Responsibilities:

- Check upcoming medication times
- Generate reminder events
- Stop reminders when treatment ends

Implementation:

- Cron Job

### Telegram Service

Responsibilities:

- Send reminder messages
- Handle delivery failures
- Log notification history

---

## Data Flow

Doctor

↓

Prescription

↓

PostgreSQL

↓

Reminder Scheduler

↓

Telegram Bot

↓

Patient

---

## Notes

This module is not implemented as an AI Agent because it does not require reasoning or decision-making.

A scheduled background service is sufficient and simpler to maintain.

---

## Notification Service

Used by multiple modules:

- Appointment Notifications
- Medication Reminders
- Feedback Requests

Channel:

- Telegram Bot API

---

## 9. Feedback Agent

Cron Job:

Runs 24 hours after appointment.

Workflow:

1. Contact patient.
2. Collect satisfaction score.
3. Collect complaints if any

4. Collect health status.
5. Store feedback.

Stored in:

- R&D Database
- Analytics Database

Used for:

- Service Improvement
- Model Fine-Tuning
- KPI Tracking

---

# Recommended Tech Stack

## Frontend

- Vue.js
- Tailwind CSS

## Backend

- FastAPI
- Python

## Agent Framework

- LangGraph

## LLM Provider

Primary:

- NVIDIA NIM API

Fallback:

- OpenRouter

## Models

Diagnosis Agent

- Qwen 3

Orchestrator Agent

- Qwen 3

Scheduling Agent

- Qwen 3

Feedback Agent

- Qwen 3

Emergency Agent

- Qwen 3

## Multimodal Models

- Qwen2.5-VL

## Speech-to-Text

- Whisper Large V3

## Text-to-Speech

MVP:

- Kokoro TTS

Future Enhancement:

- Arabic / Egyptian Arabic TTS Provider

## Vector Database

- Qdrant

## Relational Database

- PostgreSQL

## Task Scheduling

- Cron Jobs

## Monitoring

- Langfuse

## Notifications

- Telegram Bot API

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

- Authentication
- Orchestrator Agent
- Patient Database

Phase 2:

- Scheduling Agent
- Doctor Database

Phase 3:

- Medical RAG
- Diagnosis Agent

Phase 4:

- Emergency Agent

Phase 5:

- Loyalty System

Phase 6:

- Feedback Agent

Phase 8:

- Monitoring
- Analytics
- Production Deployment

---

## Clarifications & Scope Decisions (Spec Kit Clarify)

Following the specification clarification step, the following architectural and scope decisions have been finalized:

1. **Interaction Channels (MVP Scope):** The MVP will focus primarily on Text Chat and Medical Image uploads. Voice input and real-time Phone Call/IVR integrations will be simulated or deferred to a later phase.
2. **Emergency Dispatch Timer:** The emergency timer (e.g., 30s for Heart Attack, 60s for Stroke) serves as a validation window. If the patient does not cancel the alert or a clinician does not override it within that timeframe, the ambulance dispatch triggers automatically.
3. **LLM & Speech Stack:** Cloud-based models (such as GPT-4o / Claude 3.5 Sonnet) and cloud STT/TTS APIs will be used for rapid development and high reliability.
4. **Loyalty System Integration:** The loyalty points and rewards will be persisted directly in the Patient Profile table in PostgreSQL. The booking logic will automatically award points upon successful appointment completion.

