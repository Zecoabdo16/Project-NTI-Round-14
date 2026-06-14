# RAFIQ — Agentic AI Patient Companion Platform
### Arabic-First Multi-Agent Architecture for Hospital Patient Engagement
**Document type:** Architecture Blueprint  
**Scope:** Problem Statement · 9-Agent Structure & Tools · Knowledge Base Architecture · Accuracy & Evaluation Framework · 3-Week Implementation Plan

---

## 0. Design Inspiration

This architecture is grounded in two real, published multi-agent patterns:

- **MOSAIC** — a LangGraph-based clinical system built around a *plan → retrieve → annotate → verify* loop. RAFIQ reuses this loop as its safety backbone.
- **OpenQ Supervisor/Worker pattern** — a supervisor agent that routes queries to specialized workers (SQL for structured data, RAG for unstructured). RAFIQ reuses the *router + specialist workers* pattern.

RAFIQ combines both patterns across **9 agents**, giving complete coverage of patient safety, medical knowledge, operations, engagement, and analytics — while remaining realistic enough to build in 3 weeks.

---

## 1. Problem Statement

### 1.1 Context

Hospitals across Egypt and the wider region run on a mix of paper records, legacy Hospital Information Systems (HIS), siloed lab/imaging systems, and manual call centers. Patients overwhelmingly prefer Arabic (often Egyptian dialect mixed with medical terms), and most communication with the hospital happens reactively — patients calling in, queuing physically, or simply not knowing what to do next.

### 1.2 Core Pain Points

| # | Pain Point | Current Reality | Business/Clinical Impact |
|---|------------|------------------|---------------------------|
| 1 | **Wait Time** | Patients queue physically for registration, triage, billing, and results | Poor experience, overcrowding, staff burnout |
| 2 | **Availability Opacity** | Doctor schedules are not visible to patients in real time | Missed appointments, wasted trips, idle slots |
| 3 | **Call Overload** | Patients wait 15–30+ min on hold for simple questions | PBX overload, high staffing cost, patient frustration |
| 4 | **No History / Context Loss** | Every touchpoint starts from zero | Repeated tests, drug errors, patient distrust |
| 5 | **History Not Used** | EMR/CRM data never converted into actionable priority signals | A chronic patient and a first-time walk-in queued identically — clinically risky |

### 1.3 The Two Priority Signals

RAFIQ converts patient history into two live operational signals after every interaction:

- **Patient Loyalty Index (PLI)** — measures relationship value (tenure, visit frequency, adherence, satisfaction). Used for *service* prioritization only: callback order, preferred slots, proactive outreach.
- **Clinical Acuity Score (CAS)** — measures medical urgency (chronic conditions, medication complexity, recent escalations, current symptoms). Used for *clinical* queue order.

> **Governance rule:** CAS always overrides PLI for anything clinical. Loyalty influences convenience; it never delays urgent care.

### 1.4 Success Criteria

- Route >80% of routine queries to self-service agents (no human pickup).
- Every interaction begins with a grounded patient history — zero "starting from zero."
- Doctor availability and queue position visible to patients in real time.
- Auditable PLI and CAS recalculated after every visit/interaction.
- 100% sensitivity on ESI-1 triage — zero missed emergencies.

---

## 2. Solution Overview

RAFIQ is a **cyclic, stateful multi-agent graph** (LangGraph `StateGraph`) sitting between patient-facing channels and the hospital's existing systems.

```
Patient Channels (WhatsApp · Arabic Voice/IVR · Mobile App)
                          │
              ┌───────────▼────────────┐
              │   Agent 1: Supervisor  │  ← Front door: intent + dialect + routing
              └───────┬───────┬────────┘
                      │       │
          ┌───────────▼┐     ┌▼────────────┐
          │  Agent 2:  │     │  Agent 3:   │
          │   Triage   │     │ Operations  │  ← Admin / scheduling
          └─────┬──────┘     └──────┬──────┘
                │                   │
          ┌─────▼──────┐     ┌──────▼──────┐     ┌──────────────────┐
          │  Agent 4:  │     │  Agent 5:   │     │    Agent 6:      │
          │  Medical   │     │  Clinical   │     │   Verification   │
          │  Memory    │     │    DSS      │     │  + PLI/CAS       │
          └─────┬──────┘     └──────┬──────┘     └──────┬───────────┘
                └──────────────┬────┘                   │
                               ▼                        │
                    ┌──────────────────┐                │
                    │    Agent 7:      │◄───────────────┘
                    │      HITL        │  ← Doctor/Nurse dashboard
                    └──────┬───────────┘
                           │
                    ┌──────▼───────────┐
                    │ Response Composer │  ← Arabic reply
                    └──────────────────┘

Background Agents (run proactively, not per request):
  Agent 8: Patient Engagement   Agent 9: Analytics & Population Health
```

### Shared State (`PatientState`)

Every agent reads from and writes to a shared state object:

```python
PatientState = {
    "patient_id": str,
    "conversation_history": list,
    "detected_intent": str,           # admin | medical | emergency
    "urgency_level": int,             # ESI 1–5
    "emr_snippets": list,             # retrieved records with IDs
    "kg_results": list,               # graph traversal findings
    "draft_response": str,
    "grounding_confidence": float,    # 0.0–1.0
    "pli": float,                     # 0–100
    "cas": float,                     # 0–100
    "hitl_required": bool,
    "hitl_decision": str | None,
}
```

---

## 3. Agent Definitions (9 Agents)

---

### Agent 1 — Supervisor

**Role:** Front door. Classifies intent and dialect, identifies the patient, and routes to the correct specialist agent.

**NLP Layer:** CAMeL Tools / AraBERT tuned for Egyptian medical colloquialisms.

| Tool | Function | Type |
|------|----------|------|
| `detect_language_dialect` | MSA vs. Egyptian dialect vs. code-switched medical terms | Read |
| `classify_intent` | Routes to: admin, medical, or emergency | Read |
| `lookup_patient_id` | Resolves phone/national ID to patient record key | Read |
| `update_dialog_state` | Writes routing decision to shared `PatientState` | Write |

**Routing logic:**
- Emergency keywords detected → Agent 2 (Triage) immediately.
- Admin / scheduling / billing → Agent 3 (Operations).
- Medical question / labs / history → Agent 4 (Medical Memory).
- All medical responses → Agent 5 (Clinical DSS) in parallel.

---

### Agent 2 — Triage *(separated from Supervisor for safety isolation)*

**Role:** Safety-critical agent responsible exclusively for ESI classification and emergency detection. Kept isolated so it can be independently evaluated and validated by clinical staff without touching routing logic.

| Tool | Function | Type |
|------|----------|------|
| `classify_urgency_esi` | Deterministic rule-based mapping of symptom keywords to ESI 1–5 | Read |
| `detect_emergency_keywords` | Pattern match on high-urgency Arabic phrases (chest pain, breathing difficulty, bleeding) | Read |
| `flag_high_acuity` | Writes ESI level + emergency flag to `PatientState` | Write |
| `alert_hitl_emergency` | Immediately pings HITL dashboard for ESI 1–2 cases | Write |

**ESI Levels:**

| ESI | Meaning | RAFIQ Action |
|-----|---------|--------------|
| 1 | Immediate life threat | Instant HITL alert + parallel history pull |
| 2 | High risk / confused / severe pain | HITL alert + urgent slot booking |
| 3 | Urgent, stable | Route to Medical Memory + CAS spike check |
| 4–5 | Less/non-urgent | Route to Operations or self-service |

> **Design principle:** Over-triage is always preferred over under-triage. ESI 1 sensitivity target = 100%.

---

### Agent 3 — Operations & Scheduling

**Role:** Eliminates wait time, availability opacity, and call overload. Owns all interactions with the Hospital Information System (HIS).

| Tool | Function | Type |
|------|----------|------|
| `his_check_availability(doctor_id, date_range)` | Real-time slot lookup | Read |
| `his_book_appointment(patient_id, slot_id)` | Creates/updates booking | Write |
| `his_reschedule(appointment_id, new_slot_id)` | Modifies booking (e.g. doctor delay) | Write |
| `queue_position_lookup(patient_id)` | Returns live queue position + estimated wait | Read |
| `billing_status_lookup(patient_id)` | Returns invoice/insurance claim status | Read |
| `lab_result_status(patient_id, order_id)` | Returns whether results are ready (not content — that's Agent 4) | Read |
| `notify_patient(channel, template, payload)` | Sends Arabic SMS/WhatsApp confirmation | Write |

**Proactive example:** Doctor reports 30-min delay → Agent 3 automatically pushes:  
*"د. أحمد متأخر 30 دقيقة. ميعادك الجديد 2:30. اكتب 1 للتأكيد أو 2 لإعادة الحجز."*

---

### Agent 4 — Medical Memory & Knowledge

**Role:** Solves the "no history" problem. Retrieves and summarizes patient history across all knowledge layers. **Never diagnoses or prescribes — retrieves and cites only.**

| Tool | Function | Type |
|------|----------|------|
| `emr_get_patient_history(patient_id)` | Past diagnoses, surgeries, allergies, chronic conditions | Read |
| `emr_get_latest_labs(patient_id)` | Recent lab/imaging results with reference ranges | Read |
| `policy_rag_search(query)` | Vector search over hospital policy/prep-guide PDFs | Read |
| `kg_traverse_medical_graph(entities)` | Neo4j traversal: symptom → disease → medication → specialist | Read |
| `allergy_check(patient_id, new_item)` | Cross-references active medications/allergies | Read |
| `summarize_with_citations(records)` | Arabic summary where every claim cites a record ID + date | Generate |

**Strict guardrail:** All output is phrased as retrieval, never advice.  
✅ *"حسب سجلك بتاريخ 12-10-2024، عندك حساسية من البنسلين"*  
❌ *"يجب عليك أخذ..."*

---

### Agent 5 — Clinical Decision Support (DSS) *(new)*

**Role:** Reasons over what Agent 4 retrieved to detect clinical risks. Does NOT prescribe. Surfaces evidence-based alerts for the clinician only.

| Tool | Function | Type |
|------|----------|------|
| `check_drug_interactions(medication_list)` | Detects dangerous drug–drug combinations | Read |
| `check_contraindications(patient_id, new_medication)` | Validates a proposed medication against patient profile | Read |
| `recommend_specialist(symptom_list, history)` | Suggests appropriate specialist based on symptom + diagnosis graph | Read |
| `flag_clinical_alert(patient_id, alert_type, detail)` | Writes structured alert to PatientState for HITL | Write |
| `retrieve_care_pathway(diagnosis_code)` | Returns evidence-based care pathway steps | Read |

**Example:** Patient on Warfarin reports headache → Agent 5 traverses:  
*Warfarin + Ibuprofen → CONTRAINDICATED* → flags alert → routes to HITL.  
The patient is never told directly. The clinician sees the alert on their dashboard.

---

### Agent 6 — Verification, Loyalty & Priority

**Role:** Closes the MOSAIC safety loop. Every knowledge-bearing response must pass through this agent before reaching the patient. Also owns PLI/CAS computation.

| Tool | Function | Type |
|------|----------|------|
| `verify_grounding(response, source_records)` | NLI cross-encoder: every claim must be supported by a retrieved record | Read |
| `calculate_pli(patient_id)` | Computes PLI from visit frequency, tenure, lifetime value, adherence, satisfaction | Compute/Write |
| `calculate_cas(patient_id, current_visit)` | Computes CAS from chronic conditions, medication complexity, ESI history, current symptoms | Compute/Write |
| `compute_priority_rank(cas, pli)` | Merges scores per governance rule | Compute |
| `log_feedback(patient_id, rating, channel)` | Records NPS-style satisfaction score | Write |
| `schedule_followup(patient_id, reason, date)` | Creates follow-up tasks for Agent 8 | Write |

**Grounding rule:** If attribution score < 95%, the response is blocked and routed to HITL. No unverified clinical claim reaches the patient.

---

### Agent 7 — HITL (Human-in-the-Loop) *(promoted from gate to full agent)*

**Role:** Manages all human escalations. Tracks approvals, overrides, and feedback. Making this a full agent (not just a pause node) enables audit trails and disagreement analysis.

| Tool | Function | Type |
|------|----------|------|
| `push_escalation_card(patient_id, summary, urgency)` | Sends structured card to doctor/nurse dashboard | Write |
| `await_human_decision(escalation_id)` | Pauses graph until a human decision is logged | Read |
| `log_override(escalation_id, decision, staff_id)` | Records approve/reject/modify with timestamp | Write |
| `route_post_decision(decision)` | Resumes graph routing based on human decision | Write |
| `collect_hitl_feedback(escalation_id, was_appropriate)` | Records whether escalation was judged appropriate by staff | Write |

**Trigger conditions:**

| Trigger | Example |
|---------|---------|
| ESI 1–2 detected by Agent 2 | Chest pain, breathing difficulty |
| Grounding score < 95% (Agent 6) | Unsupported clinical claim in draft |
| Clinical alert from Agent 5 | Drug interaction detected |
| CAS spike vs. baseline | Known chronic patient, sudden score jump |
| Any write modifying clinical data | Prescription, triage override |

**Mechanism:** `interrupt_before` node in LangGraph — graph pauses, dashboard card is pushed, graph resumes only after the human logs a decision.

---

### Agent 8 — Patient Engagement *(new — proactive, background agent)*

**Role:** Runs independently on a schedule, not triggered by patient messages. Turns RAFIQ from a reactive system into a proactive patient companion.

| Tool | Function | Type |
|------|----------|------|
| `send_medication_reminder(patient_id, medication, time)` | Pushes Arabic WhatsApp/SMS reminder | Write |
| `send_followup_check(patient_id, reason)` | Post-discharge or post-non-compliance check-in | Write |
| `send_appointment_reminder(patient_id, appointment_id)` | 24h and 2h reminders with preparation instructions | Write |
| `send_health_tip(patient_id, condition)` | Condition-specific Arabic health education content | Write |
| `mark_engagement_event(patient_id, event_type)` | Logs interaction for PLI adherence component | Write |

**Example outputs:**  
*"لا تنس تناول دواء الضغط الساعة 8 مساءً"*  
*"كيف تشعر بعد العملية؟ اكتب 1 إذا كنت بخير أو 2 إذا تحتاج مساعدة"*  
*"نصائح مهمة لمرضى الكلى: اشرب 8 أكواب ماء يومياً"*

---

### Agent 9 — Analytics & Population Health *(new — background agent)*

**Role:** Generates hospital-level insights from aggregated patient data. This is the layer hospital management and clinical governance teams rely on.

| Tool | Function | Type |
|------|----------|------|
| `predict_no_shows(date_range)` | ML model: which appointments are likely to be missed | Compute |
| `detect_high_risk_patients()` | Flags patients with rising CAS or missed follow-ups | Compute |
| `forecast_capacity(ward, date)` | Predicts expected load per ward per day | Compute |
| `generate_satisfaction_report(period)` | Aggregates NPS/feedback trends by department | Compute |
| `detect_population_trends(condition)` | Identifies condition clusters across patient cohort | Compute |
| `export_dashboard_data(format)` | Pushes insights to hospital BI dashboard | Write |

**Example insights:**  
- "37 patients with diabetes have not had an HbA1c check in 6 months."  
- "Nephrology ward predicted at 140% capacity this Thursday."  
- "No-show risk: 12 appointments tomorrow are flagged as high-risk."

---

## 4. Knowledge Base Architecture (4 Layers)

A single vector index cannot represent relationships (drug interactions) or time-series facts (lab trends). RAFIQ uses a **4-layer federated knowledge architecture**.

```
Incoming Query → Retrieval Router
                      │
      ┌───────────────┼───────────────┬──────────────┐
      ▼               ▼               ▼              ▼
  Layer 1         Layer 2         Layer 3        Layer 4
  Vector RAG      GraphRAG        Structured     Session
  (Qdrant)        (Neo4j)         (PostgreSQL)   (Redis)
  Policies        Drug graph      EMR + Labs     Session
  FAQs            Symptom→Spec.   Visit history  state
  Prep guides     Care pathways   Billing        cache
      │               │               │              │
      └───────────────┴───────────────┴──────────────┘
                              │
                    Context Bundle (with provenance tags)
                              │
                       Agent 4 / Agent 6
```

### Layer 1 — Vector RAG (Qdrant / pgvector)
- **Content:** Hospital policies, insurance rules, pre-procedure guides, FAQs.
- **Use case:** *"إيه اللي يجب أعمله قبل عمل MRI للركبة؟"* → returns relevant PDF section in Arabic.

### Layer 2 — GraphRAG (Neo4j)
- **Why needed:** Vector search returns similar documents. Graph traversal follows relationship chains.
- **Schema:** Nodes: `Patient · Symptom · Disease · Medication · Specialist · Procedure` / Edges: `PRESCRIBED · CONTRAINDICATED_WITH · DIAGNOSED_WITH · REQUIRES_SPECIALIST · PRECEDES`
- **Use case:** *Patient → Warfarin → Headache → Ibuprofen → CONTRAINDICATED* → alert to clinician.

### Layer 3 — Structured / Temporal Store (PostgreSQL)
- **Content:** Longitudinal EMR — visit history, diagnoses over time, lab trends, billing, insurance.
- **Primary consumers:** Agent 4 (history retrieval), Agent 6 (PLI/CAS computation), Agent 9 (population analytics).

### Layer 4 — Episodic Session Memory (Redis)
- **Content:** Short-term conversational state within a single session. Prevents re-asking what the patient already said. In-flight booking drafts, deduplication of repeated questions.

---

## 5. PLI & CAS Scoring

### 5.1 Patient Loyalty Index (PLI) — 0 to 100

```
PLI = 0.30 × VisitFrequencyScore
    + 0.15 × RelationshipTenureScore
    + 0.20 × LifetimeValueScore
    + 0.20 × TreatmentAdherenceScore
    + 0.15 × SatisfactionScore
```

**Use:** Service queue order only — callback priority, preferred slot offers, proactive check-in eligibility. PLI never affects clinical queue order.

### 5.2 Clinical Acuity Score (CAS) — 0 to 100

```
CAS = 0.40 × CurrentESI (inverted: ESI 1 = highest score)
    + 0.20 × SymptomKeywordUrgencyMatch
    + 0.15 × ChronicConditionCount
    + 0.15 × RecentEscalationRecency
    + 0.10 × MedicationComplexity
```

Current symptoms (ESI + keyword match) contribute 60% of the score. Chronic history adds context but does not override an acute presentation.

### 5.3 Governance Rule

```
New interaction arrives
        │
        ▼
CAS ≥ high-acuity threshold?
        │
   YES  │  NO
   ▼         ▼
Clinical    Service
Priority    Queue
Queue       (PLI order)
(CAS order) │
│           │
└─────┬─────┘
      ▼
Audit log: score components + weight version + timestamp
```

Every PLI/CAS computation is logged with its inputs and weight version for bias audits and clinical governance review. Weight changes require a versioned sign-off.

---

## 6. End-to-End Example Flow

**Patient message:** *"يا دكتور أنا مخدتش العلاج بتاعي وضهري وجعني تاني"*  
*("Doctor, I didn't take my medication and my back hurts again")*

```
Patient (WhatsApp)
    │
    ▼
Agent 1 (Supervisor)
  → detect_language_dialect: Egyptian dialect
  → classify_intent: medical + non-compliance
  → lookup_patient_id: Patient 4821
  → route to Agent 2 + Agent 4
    │
    ├──► Agent 2 (Triage)
    │      → classify_urgency_esi: ESI 3 (urgent, not immediate)
    │      → writes urgency=3 to PatientState
    │
    └──► Agent 4 (Medical Memory)
           → emr_get_patient_history: CKD, last visit 2 weeks ago, Drug X
           → kg_traverse_medical_graph: Drug X cannot be stopped abruptly → FLAGGED
           → summarize_with_citations: Arabic draft with record IDs
           │
           ▼
        Agent 5 (Clinical DSS)
           → check_drug_interactions: Drug X abrupt cessation → risk confirmed
           → flag_clinical_alert: "CKD + missed dose + back pain"
           │
           ▼
        Agent 6 (Verification)
           → verify_grounding: 97% attribution ✓
           → calculate_cas: score = 78 → above threshold
           → triggers HITL
           │
           ▼
        Agent 7 (HITL — Nephrology Desk)
           Dashboard card: "Patient 4821 · CKD · missed dose · Drug X risk · back pain"
           Nurse decision: "Book urgent nephrology slot"
           │
           ▼
        Agent 3 (Operations)
           → his_check_availability: slot at 3:00 PM with Dr. Tarek
           → his_book_appointment: confirmed
           → notify_patient: WhatsApp Arabic confirmation
           │
           ▼
        Agent 6 (post-interaction)
           → schedule_followup: +3 days (non-compliance check)
           → update PLI: adherence component adjusted down
           → log interaction

Patient receives:
"تم حجز موعد عاجل مع د. طارق (أمراض الكلى) اليوم الساعة 3:00 م.
 يرجى إحضار قائمة أدويتك."
```

**Total time: under 60 seconds. Zero phone calls. Clinician stayed in the loop.**

---

## 7. Accuracy & Evaluation Framework

| Area | Metric | Method | Target |
|------|--------|--------|--------|
| Routing (Agent 1) | Intent accuracy | Confusion matrix vs. human-labeled utterance set | ≥ 90% |
| Triage safety (Agent 2) | ESI-1 sensitivity | True-urgent / (True-urgent + False-non-urgent) on 100+ cases | **100%** |
| Grounding (Agents 4 + 6) | Attribution rate | NLI cross-encoder: every claim traces to a record ID | ≥ 95% |
| Hallucination (Agent 4) | Unsupported-claim rate | Same NLI pipeline | < 5% |
| Drug safety (Agent 5) | Contraindication recall | Against curated interaction database | ≥ 99% |
| Call deflection (Agents 3 + 4) | Deflection rate | Resolved without human / total queries | > 80% |
| Scheduling (Agent 3) | Booking success rate | `his_book_appointment` success, zero double-bookings | ≥ 98% |
| KG quality (Layer 2) | Entity resolution F1 | Entity linking + contraindication edge recall | ≥ 0.90 |
| PLI/CAS validity (Agent 6) | Cohen's kappa vs. nurse ranking | κ between CAS queue order and nurse triage ranking | κ ≥ 0.75 |
| HITL effectiveness (Agent 7) | Escalation recall | % of true high-acuity cases escalated | **100%** |
| Engagement (Agent 8) | Reminder response rate | % of patients who confirm/respond | ≥ 60% |
| Analytics (Agent 9) | No-show prediction AUC | ROC AUC on held-out appointment set | ≥ 0.80 |
| Latency | End-to-end P95 | Retrieval-only: < 6s / Scheduling lookup: < 2s | Per target |

### Continuous Evaluation Pipeline

```
Golden Test Set ──► Run Agent Graph (shadow mode) ──► Automated Evaluators
      ▲                                                        │
      │                                              Evaluation Dashboard
      │                                                        │
Live Interactions ──► HITL Decisions ──► Re-labeling Queue    │
                                                    │          ▼
                                                    └──► Drift Alerts ──► Retrain
```

- **Golden Set:** De-identified historical cases + synthetic Egyptian-dialect variants.
- **Shadow mode:** New model versions run against live traffic without affecting responses, scored before promotion.
- **HITL disagreements** are the highest-value re-labeling signal, reviewed weekly.

---

## 8. Technology Stack

| Component | Technology |
|-----------|------------|
| Agent orchestration | LangGraph (cyclic `StateGraph`) |
| LLM | Arabic-capable instruction model (dialect fine-tuned) |
| Arabic NLP | CAMeL Tools / AraBERT family |
| Vector RAG | Qdrant or pgvector |
| GraphRAG | Neo4j |
| Structured store | PostgreSQL + time-series extensions |
| Session memory | Redis |
| Grounding verification | `nli-deberta-v3-small` cross-encoder |
| HIS/EMR integration | FHIR adapters where available, custom HIS connectors otherwise |
| Notifications | WhatsApp Business API + SMS gateway |
| HITL dashboard | Internal web app (clinician-facing queue + override UI) |
| Analytics BI | Grafana or hospital-provided BI tool |

---

## 9. 3-Week Implementation Roadmap

> **Strategy:** Build the narrowest working vertical first (one real patient query end-to-end), then layer in agents. Every week ends with something you can demo.

---

### Week 1 — Working Skeleton (Demo-able by Day 7)

**Goal:** A patient can send an Arabic WhatsApp message, get routed correctly, and receive a scheduling reply.

| Day | Task | Agents / Layers |
|-----|------|-----------------|
| 1 | Set up LangGraph `StateGraph` + `PatientState` schema. Mock all tool calls with static JSON. | Infrastructure |
| 1 | Set up local Neo4j, PostgreSQL, Redis, and Qdrant instances with seed data. | KB Layers 1–4 |
| 2 | Build **Agent 1 (Supervisor):** intent classifier + dialect detection using AraBERT or CAMeL. | Agent 1 |
| 2–3 | Build **Agent 2 (Triage):** ESI keyword rules + emergency alert stub. | Agent 2 |
| 3–4 | Build **Agent 3 (Operations):** HIS mock + slot booking + WhatsApp notification. | Agent 3 |
| 5 | Wire Agents 1 → 2 → 3 in the state graph. Test full admin flow end-to-end. | Integration |
| 6 | Load 20 hospital policy PDFs into Layer 1 (Qdrant). Test `policy_rag_search`. | Layer 1 |
| 7 | **Week 1 demo:** Patient asks about appointment availability → Agent 1 routes → Agent 3 books → WhatsApp reply. | Demo |

**Week 1 exit criteria:**
- Admin intent routed correctly ≥ 90% on a 20-utterance test set.
- Booking flow completes end-to-end with mocked HIS.
- WhatsApp message delivered in Arabic.

---

### Week 2 — Medical Intelligence + Safety (Demo-able by Day 14)

**Goal:** Medical history retrieval works, drug interactions are caught, and the HITL dashboard is live.

| Day | Task | Agents / Layers |
|-----|------|-----------------|
| 8 | Build **Agent 4 (Medical Memory):** EMR retrieval from PostgreSQL + `summarize_with_citations`. | Agent 4 |
| 8–9 | Load Layer 3 (PostgreSQL) with 10 de-identified patient records. Load Layer 2 (Neo4j) with basic drug graph. | Layers 2–3 |
| 9–10 | Build **Agent 5 (Clinical DSS):** drug interaction checker using Neo4j graph traversal. | Agent 5 |
| 10–11 | Build **Agent 6 (Verification):** NLI grounding check + PLI/CAS computation. | Agent 6 |
| 11–12 | Build **Agent 7 (HITL):** `interrupt_before` node + simple clinician dashboard (web app). | Agent 7 |
| 12–13 | Wire Agents 4 → 5 → 6 → 7 into the graph. Test medical flow with CKD patient scenario. | Integration |
| 14 | **Week 2 demo:** CKD patient misses medication → history retrieved → drug risk flagged → CAS computed → HITL dashboard alert → doctor approves urgent slot. | Demo |

**Week 2 exit criteria:**
- Grounding attribution ≥ 95% on 15 medical Q&A test cases.
- ESI-1 recall = 100% on a 30-case triage test set.
- At least one drug interaction correctly caught and routed to HITL.
- PLI and CAS computed and logged for 10 test patients.

---

### Week 3 — Proactive Agents + Evaluation + Polish (Demo-able by Day 21)

**Goal:** Background agents are running, the evaluation pipeline is live, and the full system is demo-ready.

| Day | Task | Agents / Layers |
|-----|------|-----------------|
| 15–16 | Build **Agent 8 (Patient Engagement):** scheduled reminders + follow-up messages via WhatsApp. | Agent 8 |
| 16–17 | Build **Agent 9 (Analytics):** no-show prediction (basic ML) + capacity forecast + satisfaction report. | Agent 9 |
| 17–18 | Build evaluation pipeline: golden test set (50 labeled utterances) + automated NLI grounding scorer + routing confusion matrix. | Evaluation |
| 18–19 | Integrate real (or realistic mock) HIS/FHIR adapter. Replace all static mocks with live tool calls. | Integration |
| 19–20 | Run shadow-mode evaluation on all 9 agents. Fix top failing cases. | Testing |
| 20 | Prepare final demo script: 3 scenarios (routine booking, CKD non-compliance, drug interaction emergency). | Demo prep |
| 21 | **Final demo:** Full 9-agent system running live, evaluation dashboard showing metrics, HITL dashboard visible. | Final demo |

**Week 3 exit criteria:**
- All 9 agents integrated and running end-to-end.
- Evaluation dashboard showing ≥ 5 metrics with targets.
- Agent 8 sends at least one scheduled reminder successfully.
- Agent 9 generates at least one analytics report.
- P95 latency < 6s for medical queries, < 2s for scheduling.

---

## 10. Agent Summary Table

| # | Agent | Priority | Addresses Pain Point | Week Added |
|---|-------|----------|----------------------|------------|
| 1 | Supervisor | Essential | All (routing) | Week 1 |
| 2 | Triage | Essential (safety-critical) | #1 Wait time, emergencies | Week 1 |
| 3 | Operations | Essential | #1 #2 #3 | Week 1 |
| 4 | Medical Memory | Essential | #4 No history | Week 2 |
| 5 | Clinical DSS | Strong addition | #4 Drug safety | Week 2 |
| 6 | Verification + PLI/CAS | Essential | #5 Priority blindness | Week 2 |
| 7 | HITL | Essential | Safety compliance | Week 2 |
| 8 | Patient Engagement | Strong addition | #3 #4 Proactive care | Week 3 |
| 9 | Analytics | Advanced addition | Hospital operations | Week 3 |

---

## 11. Key Design Principles

1. **Router + Specialist Workers** — Agent 1 routes; specialist agents (2–5) own their domain completely.
2. **Plan → Retrieve → Verify** — Agent 6 closes the loop on every knowledge response before it reaches the patient.
3. **Retrieval only for medical content** — Agent 4 cites; it never advises. Agent 5 alerts; it never prescribes.
4. **Safety over loyalty** — CAS always overrides PLI for clinical queue order. Loyalty governs convenience only.
5. **Triage isolation** — Agent 2 is kept separate from Agent 1 so it can be independently validated and replaced without touching routing.
6. **HITL as a full agent** — Agent 7 is not a passive pause. It tracks decisions, collects override feedback, and feeds disagreements back into the evaluation pipeline.
7. **Everything is measured** — routing accuracy, triage sensitivity, grounding attribution, scheduling reliability, drug recall, PLI/CAS validity, engagement rate, and analytics AUC all have explicit targets and a continuous evaluation loop.
