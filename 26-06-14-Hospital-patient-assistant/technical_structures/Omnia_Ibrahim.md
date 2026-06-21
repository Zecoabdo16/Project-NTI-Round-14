# Comprehensive Technical & AI Implementation Plan: Agentic Patient Assistant

> [!NOTE]
> This document represents the unified master plan for the Patient Assistant. It seamlessly integrates the AI/Agentic logic with the foundational software engineering, infrastructure, and deployment architecture to provide a holistic view of the entire project.

---

# 1. System Architecture & Core Layers

The system relies on a highly decoupled architecture, ensuring that the AI reasoning layers are safely integrated with traditional software infrastructure.

## 1.1 Communication Layer (Interfaces)

- **WhatsApp / Messaging Integration**: Using unofficial libraries (e.g., `whatsapp-web.js` or `Baileys`) or Telegram Bot API for 100% free bilingual (Arabic/English) text conversations.
- **Voice Gateway**: Open-source Interactive Voice Response (IVR) like Asterisk or FreeSWITCH integrated with local STT/TTS for elderly patients.
- **Website Widget**: A custom React/Vanilla JS chat interface via WebSockets.
- **Receptionist Dashboard**: A secure internal web dashboard (React/Next.js) receiving real-time clinical alerts via SSE.

## 1.2 Orchestration & State Management

- **Framework**: **LangGraph** orchestrates the multi-agent workflow, graph state, memory, and transitions.
- **State Object (LangGraph State)**: Data is passed between agents using a unified State dictionary (Shared Memory) containing:
  - `messages`: Conversation history and agent responses.
  - `patient_id`: Verified EMR ID.
  - `current_intent`: User's main goal (e.g., booking, triage).
  - `extracted_symptoms`: List of symptoms for the Triage Agent.
  - `missing_fields`: Flags for the Missing Data Handler.
- **State Store**: **Redis** for managing active conversation state and short-term memory between agent nodes, and **PostgreSQL** for session persistence and long-term memory.

## 1.3 Integration Layer (Data Exchange)

- **EMR/EHR System**: Deep integration via **HAPI FHIR API** (Open-source FHIR server) to read patient profiles and write appointments.
- **Loyalty & Analytics DB**: An internal database tracking points, referrals, and NPS survey results.

---

# 2. Multi-Agent System Design

The system is powered by 8 specialized LLM-driven agents working in an assembly-line fashion.

1. **Supervisor Agent**
   - **Input:** Raw User Message, Conversation History.
   - **Output:** Routing Decision (Next Agent to invoke).
2. **Patient Onboarding Agent**
   - **Input:** Intent to register for the first time.
   - **Output:** Structured Patient Profile Data (Name, Phone, DOB).
3. **Identity Verification Agent**
   - **Input:** Phone Number or National ID.
   - **Output:** Verified EMR Patient ID OR a flag indicating unregistered user.
4. **Missing Data Handler**
   - **Input:** Missing data fields (e.g., missing Age for booking).
   - **Output:** Completed data points gathered from the user.
5. **Triage Agent (4 Sub-agent Pipeline)**
   - **Input:** Patient's described symptoms.
   - **Output:** Urgency Level, Recommended Medical Specialty, and Clinical Note.
6. **Scheduling Agent**
   - **Input:** Patient ID, Target Specialty, Preferred Time.
   - **Output:** Confirmed Appointment ID and confirmation message.
7. **Care Coordinator Agent**
   - **Input:** Completed appointment trigger.
   - **Output:** Follow-up instructions, Loyalty Points updates, and NPS Survey link.
8. **Human Handoff Agent**
   - **Input:** Escalation trigger (Emergency / Human request), Chat History.
   - **Output:** Escalation Ticket routed to the Receptionist Dashboard.

## 2.1 Agent Toolsets (Custom AI Tools)

- `SearchEMRTool`
- `CreatePatientProfileTool`
- `ValidateSymptomsTool`
- `CheckAvailabilityTool`
- `BookAppointmentTool`
- `SendMessageTool`
- `TriggerDashboardAlertTool`

## 2.2 Conversation Flow Example (Patient Journey)

**Scenario: A new patient feels sick and wants to book an appointment.**

1. **User Message:** "أشعر بألم شديد في الصدر وأريد حجز موعد."
2. **Supervisor Agent:** Analyzes the message and routes to **Identity Verification Agent**.
3. **Identity Verification Agent:** Asks for phone number, fails to find the patient in EMR. Routes to **Patient Onboarding Agent**.
4. **Patient Onboarding Agent:** Collects Name and Phone, then updates the LangGraph State with a new `patient_id`.
5. **Supervisor Agent:** Reads the updated state, sees the user mentioned "ألم شديد في الصدر", and routes to **Triage Agent**.
6. **Triage Agent:** Analyzes the symptom. Flags it as a high urgency (Emergency) and updates the State.
7. **Supervisor Agent:** Reads the Emergency flag. Routes immediately to **Human Handoff Agent**.
8. **Human Handoff Agent:** Sends an urgent ticket to the receptionist dashboard and tells the patient: "تم تحويلك فوراً لموظف الاستقبال لخطورة الحالة."

---

# 3. AI Engineering Layer

## 3.1 Prompting Strategy

- Meta/System Prompts
- Task-Specific Prompts

## 3.2 Context Window Management

- Data Minimization
- Rolling Memory

## 3.3 AI Safety & Guardrails

- Clinical Boundary Enforcement
- Output Validation
- Hallucination Mitigation

## 3.4 Evaluation & Testing (AI Metrics)

- LLM-as-a-Judge
- Safety Benchmarks (Red-teaming)

---

# 4. Comprehensive Technology Stack

| Category | Recommended Technologies (100% Free / Open Source) |
|-----------|----------------------------------------------------|
| AI & LLM Provider | Llama 3, Qwen, or Mistral (Self-hosted locally via Ollama / vLLM) |
| Speech Models (STT/TTS) | Local OpenAI Whisper (`whisper.cpp`), Piper, or Edge-TTS |
| AI Observability | Langfuse (Self-hosted) or Phoenix |
| Agent Orchestration | LangChain / LangGraph |
| Backend API Framework | FastAPI or NestJS |
| Frontend Framework | React.js / Next.js with TailwindCSS |
| Databases | PostgreSQL + Redis |
| Integration Standards | HAPI FHIR |
| Infrastructure | On-Premise Servers |
| DevOps & CI/CD | GitLab CI/CD, Prometheus + Grafana |

---

# 5. Security & Compliance (HIPAA-Aligned)

1. TLS 1.3 + AES-256 Encryption
2. Data Minimization
3. Audit Trails
4. RBAC + MFA
5. Data Sovereignty

---

# 6. Implementation Phasing

## Phase 1A: Pilot (Months 1–2)

- WhatsApp text channel
- Identity Check
- Triage
- Human Handoff

## Phase 1B: Booking & Live EMR (Months 3–4)

- Scheduling Agent
- HAPI FHIR Integration

## Phase 1C: Retention (Months 5–6)

- Care Coordinator Agent
- Loyalty System
- NPS Tracking

## Phase 2: Scale (Month 7+)

- Voice Integration
- Multi-department Support
- Advanced Analytics Dashboard
