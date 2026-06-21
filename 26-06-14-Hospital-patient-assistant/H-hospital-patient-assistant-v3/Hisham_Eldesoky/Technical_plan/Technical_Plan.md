# Technical Plan — Agentic Medical System (v2)
### Requirements, Component I/O Specification, and LLM Selection

**Companion to:** `system_design.md`
**Purpose:** This document breaks the architecture into independently buildable components, defines exact input/output contracts for each, and recommends a model for each based on what that component actually needs (reasoning depth, latency, determinism, or multimodal capability) rather than defaulting to one frontier model everywhere.

---

## 1. Functional Requirements

The system must support text and medical-image input from patients (voice/phone deferred). It must authenticate a patient and maintain session state across a conversation. It must classify incoming requests as scheduling or medical, and route accordingly. It must check real doctor/department availability and complete or reschedule bookings, with a graceful fallback when nothing is available. It must accept multi-modal symptom descriptions and normalize them into structured data. It must produce a deterministic, auditable urgency classification before any reasoning step touches the case. It must ground every diagnosis-adjacent claim in the patient's actual records and check for medication contraindications before that claim can trigger any action. It must detect emergencies and notify a human clinician in parallel with any automated countdown, never only after one expires. It must escalate to a human reviewer whenever confidence is low, claims are ungrounded, symptoms conflict, or a contraindication is found. It must track loyalty points and run a post-visit feedback check-in without blocking or competing with clinical flow. Every triage, safety, and dispatch decision must be logged for audit.

## 2. Non-Functional Requirements

| Requirement | Target |
|---|---|
| Orchestrator routing latency | < 1s P95 |
| Scheduling lookup latency | < 2s P95 |
| Diagnosis reasoning latency | < 6s P95 |
| Emergency decision latency | < 1s P95 (this is the one place sub-second matters most) |
| ESI-1-equivalent sensitivity (life-threat recall) | 100% |
| Grounding attribution rate | ≥ 95% |
| Contraindication recall | ≥ 99% |
| Routing/intent classification accuracy | ≥ 90% |
| Data residency / compliance | TBD per deployment market — see Section 6 |

---

## 3. Component Specifications

### 3.1 Orchestrator Agent

**Requirements:** Authenticate the patient across channels, resolve identity, maintain session state, and classify the incoming request as scheduling or medical. This runs on every single message, so cost and latency dominate over reasoning depth.

| | |
|---|---|
| **Input** | `{channel, raw_message, patient_identifier [phone or national_id or session_token], timestamp}` |
| **Output** | `{patient_id, session_id, request_type [scheduling \| medical_complaint], routed_to, auth_status}` |
| **Recommended LLM** | Fast/cheap tier only — Claude Haiku 4.5, GPT-5.4 mini, or Gemini 3.1 Flash-Lite. Identity resolution itself is a database lookup, not an LLM task; the model's only job is intent classification. |
| **Self-hosted alternative** | Gemma 4 (4B–12B) if data residency requires on-prem inference. |

### 3.2 Scheduling Agent

**Requirements:** Interpret natural-language scheduling requests, query doctor availability, book or reschedule, and suggest alternatives when nothing is available.

| | |
|---|---|
| **Input** | `{patient_id, request_text, department_or_doctor_id (optional), preferred_date_range (optional)}` |
| **Output** | `{available_slots[]}` **or** `{booking_confirmation: {appointment_id, doctor, datetime}}` **or** `{alternative_suggestion}` |
| **Recommended LLM** | Fast/cheap tier with reliable function calling — Claude Haiku 4.5 or GPT-5.4 mini. The availability query is plain code; the model only needs to parse intent and confirm slot selection conversationally. |

### 3.3 Symptom Intake Agent

**Requirements:** Normalize multi-modal complaint input (text and optional medical image) into structured symptom data. This is the one agent in the conversational path that genuinely needs strong vision capability.

| | |
|---|---|
| **Input** | `{patient_id, complaint_text, image (optional), channel}` |
| **Output** | `{structured_symptoms: [{symptom, body_location, duration, self_reported_severity}], extracted_entities, image_findings (if applicable)}` |
| **Recommended LLM** | Gemini 3.1 Pro or GPT-5.5 (both vision-capable with strong multimodal benchmarks) or Claude Sonnet 4.6. |
| **Self-hosted alternative** | Qwen3-VL or GLM-4.6V for on-prem multimodal inference. |
| **Caution** | Any image suggestive of something needing real diagnostic imaging (not a visible external symptom) should route straight to HITL — a general vision-language model is not a substitute for radiology-grade analysis. |

### 3.4 Triage Agent

**Requirements:** Deterministic-first urgency scoring, isolated from the reasoning agent so it can be independently validated. This is the single highest-stakes component in the system — 100% sensitivity on life-threat cases is non-negotiable.

| | |
|---|---|
| **Input** | `{structured_symptoms, patient_age, known_chronic_flags (lightweight, not full history)}` |
| **Output** | `{urgency_level [ESI 1-5 equivalent], triggered_keywords, confidence}` |
| **Recommended approach** | Keep the LLM's role narrow — structured field extraction only. The actual urgency mapping should run through a deterministic rules engine (keyword/symptom-to-ESI lookup) in code, not free-form LLM judgment. If a model is used for extraction, use a small model in strict JSON-output mode at temperature 0: Claude Haiku 4.5 or GPT-5.4 mini. Avoid frontier "creative" models here — predictability matters more than depth. |

### 3.5 Diagnosis Reasoning Agent

**Requirements:** Synthesize patient EMR history, medical RAG context, and structured symptoms into a candidate department/diagnosis with a confidence score. This is the component that genuinely needs frontier-level reasoning and a large context window.

| | |
|---|---|
| **Input** | `{structured_symptoms, emr_history_snippets[], rag_context_chunks[], urgency_level}` |
| **Output** | `{candidate_diagnosis, candidate_department, confidence_score, cited_sources[]}` |
| **Recommended LLM** | Claude Opus 4.6/4.7 or Gemini 3.1 Pro — both currently lead graduate-level science reasoning benchmarks (GPQA Diamond), a reasonable proxy for the kind of multi-step clinical reasoning this agent does. GPT-5.5 is a credible alternative given its emphasis on long-horizon agentic reliability. |
| **Cost-tier fallback** | Claude Sonnet 4.6 if Opus-tier cost is prohibitive at conversation volume. |
| **Self-hosted** | Not recommended for this specific agent — the open-weight gap is still largest on deep multi-step clinical reasoning, and this is exactly the component where a reasoning error matters most. |

### 3.6 Clinical Safety Check

**Requirements:** Verify every claim in the diagnosis draft is grounded in retrieved records (not hallucinated), and check for medication/condition contraindications against the patient's active medications and allergies.

| | |
|---|---|
| **Input** | `{draft_diagnosis_text, cited_sources[], patient_active_medications[], patient_allergies[]}` |
| **Output** | `{grounding_score [0-1], contraindication_flags[], pass_fail}` |
| **Recommended approach** | This is better served by a dedicated NLI cross-encoder (e.g. a `deberta-v3`-class entailment model) for grounding scoring than a general chat LLM — it's a narrower, more consistent task and far cheaper to run at this volume. Contraindication checking is a graph/rule lookup against a curated interaction database, not an LLM judgment call. |
| **If LLM needed** | Only for drafting the human-readable explanation of a flagged issue for the clinician — a small fast model suffices (Claude Haiku 4.5 / GPT-5.4 mini). |

### 3.7 Emergency Agent

**Requirements:** Near-real-time dispatch decision, parallel clinician notification, and a short patient-facing message. Latency dominates here more than anywhere else in the system.

| | |
|---|---|
| **Input** | `{urgency_level=Life-threat, patient_id, known_chronic_risk_profile}` |
| **Output** | `{dispatch_decision [immediate \| timed], timer_seconds (if timed), clinician_alert_payload, patient_message}` |
| **Recommended LLM** | Fastest available tier — Claude Haiku 4.5, GPT-5.4 nano/mini, or Gemini 3.1 Flash-Lite. |
| **Design note** | The dispatch decision itself should be rule-based against the documented risk profile, not an LLM judgment call — the model's only job is generating the calm patient-facing message quickly while the rule engine and clinician notification fire in parallel. |

### 3.8 HITL (Human Doctor Review)

**Requirements:** Produce a clear, well-cited clinical summary for a human reviewer. Summarization quality matters more than raw speed here, since a clinician is reading it rather than waiting on a live chat.

| | |
|---|---|
| **Input** | `{patient_summary_data, emr_history_snippets[], structured_symptoms, candidate_diagnosis, safety_check_result}` |
| **Output** | `{formatted_summary_card, suggested_department, escalation_reason}` |
| **Recommended LLM** | Claude Sonnet 4.6 or GPT-5.4 standard — strong summarization quality without flagship pricing, since this isn't latency-bound. |

### 3.9 Loyalty Agent

**Requirements:** Update loyalty points on booking completion and optionally generate personalized offer text. Almost entirely deterministic business logic.

| | |
|---|---|
| **Input** | `{patient_id, booking_completion_event, current_loyalty_balance}` |
| **Output** | `{updated_balance, offer_text (optional)}` |
| **Recommended LLM** | Minimal — point calculation should be plain code. If offer text generation is wanted, a cheap small model suffices (Claude Haiku 4.5 / GPT-5.4 nano). No frontier model needed anywhere in this agent. |

### 3.10 Feedback Agent

**Requirements:** Run a post-visit check-in 24 hours after an appointment, collect satisfaction and health status, and lightly classify the sentiment/urgency of free-text responses.

| | |
|---|---|
| **Input** | `{patient_id, appointment_id, patient_free_text_response}` |
| **Output** | `{satisfaction_score, health_status_flag, sentiment_classification, escalation_needed}` |
| **Recommended LLM** | Cheap/fast tier — Claude Haiku 4.5 or GPT-5.4 mini. |
| **Design note** | `escalation_needed` matters more than it looks — if a feedback response indicates the patient is doing worse, that should loop back into the Triage/Emergency path, not just sit in an analytics table unread. |

---

## 4. LLM Selection — Consolidated

| Agent | Primary Recommendation | Why | Self-Hosted Alternative |
|---|---|---|---|
| Orchestrator | Claude Haiku 4.5 / GPT-5.4 mini | High volume, low reasoning need, latency-critical | Gemma 4 (4B–12B) |
| Scheduling | Claude Haiku 4.5 / GPT-5.4 mini | Tool-calling reliability over reasoning depth | Gemma 4 / Qwen3.5 |
| Symptom Intake | Gemini 3.1 Pro / GPT-5.5 / Claude Sonnet 4.6 | Vision capability is the binding constraint | Qwen3-VL / GLM-4.6V |
| Triage | Claude Haiku 4.5 / GPT-5.4 mini (extraction only) | Determinism > creativity for safety-critical scoring | Gemma 4 (extraction only) |
| Diagnosis Reasoning | Claude Opus 4.6/4.7 / Gemini 3.1 Pro | Deepest reasoning need in the system | Not recommended |
| Clinical Safety Check | Dedicated NLI cross-encoder (non-chat model) | Narrow, consistent scoring task, not generative | Same — open NLI models are adequate here |
| Emergency | Claude Haiku 4.5 / GPT-5.4 nano | Sub-second latency is the dominant constraint | Gemma 4 |
| HITL Summary | Claude Sonnet 4.6 / GPT-5.4 standard | Summarization quality, not latency-bound | — |
| Loyalty | None / Claude Haiku 4.5 for optional copy | Pure business logic | — |
| Feedback | Claude Haiku 4.5 / GPT-5.4 mini | Low-stakes conversational check-in | Gemma 4 |

---

## 5. Compliance & Data Residency

This system handles real patient health data, which changes the model-selection calculus beyond raw capability. Before finalizing vendor choice for any agent that touches EMR data (Diagnosis Reasoning, Clinical Safety Check, Symptom Intake, HITL), confirm: which jurisdictions the hospital operates in and what data residency rules apply there; whether the chosen API provider offers an enterprise agreement covering health-data processing in that jurisdiction; and whether any agents must run fully on-prem or in a private cloud instead of calling an external API at all. This is a decision for legal/compliance sign-off, not an engineering default — the self-hosted alternatives listed above exist specifically so that path is available without a full re-architecture if required.

---

## 6. Open Decisions

The cost ceiling per conversation (which determines how often the Diagnosis Reasoning Agent can justify frontier-tier pricing vs. falling back to Sonnet-tier) needs a number from whoever owns the budget. The self-host vs. API decision for EMR-touching agents depends on the compliance answer above and should be resolved before Week 2 of the build (per the system design's phasing), since it affects infrastructure provisioning. Finally, the Clinical Safety Check's NLI model needs an actual model selected and benchmarked against a labeled grounding test set before its 95% attribution target can be verified rather than assumed.