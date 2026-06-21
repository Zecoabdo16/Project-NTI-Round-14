# Patient Assistant AI — Cleopatra Hospital
## Technical Plan (MVP) — Descriptive Edition

**Framework:** OpenAI Agents SDK · **Model:** OpenAI · **Database:** PostgreSQL + pgvector (single store)
**Version:** 1.3 · **Date:** June 2026

This version explains the same MVP architecture as a narrative, organized by: Database → Database Tables → Expected User Load → Framework → OpenAI Models → Agents → Tools → Deployment → Prompt Engineering Framework → Project Folder Structure. No code — this is meant for planning, stakeholder review, and team alignment before implementation starts.

---

## 1. Database

**Choice: a single PostgreSQL instance with the `pgvector` extension enabled.**

The original business plan called for three separate systems: PostgreSQL for structured data, ChromaDB for vector search, and Redis for session memory. For the MVP, all three responsibilities are consolidated into one Postgres database:

- **Structured data** (patients, doctors, appointments, complaints, loyalty, tourism) lives in ordinary relational tables.
- **Knowledge base content** (medical articles, emergency triage rules, tourism packages) lives in tables that include a vector column. Postgres searches these by semantic similarity using `pgvector`, the same way a dedicated vector database would, but without a second system to run.
- **Conversation memory** (what the patient and the agents said to each other) is stored in Postgres as well, using a session-storage feature built into the OpenAI Agents SDK that is database-agnostic and happens to support Postgres natively.

**Why this matters for an MVP:** one database means one connection pool, one backup job, one thing to monitor, and one bill. It removes an entire category of "is Redis up, is ChromaDB up" failure modes during the period when the team should be focused on whether the agents behave correctly. If usage later grows to the point where a dedicated vector database or a Redis cache genuinely improves performance, that can be added without rewriting any agent logic — it's a swap underneath an existing interface, not a redesign.

---

## 2. Database Tables

| Table | Purpose | Who reads | Who writes |
|---|---|---|---|
| `patients` | Core patient identity, contact info, preferences, non-clinical notes, and a `reengagement_flagged` boolean for marketing outreach | All agents (for context) | CRM Agent; Loyalty Agent (flag only) |
| `doctors` | Doctor profiles: specialty, rating, location, referral/document requirements, on-call status | Booking Agent, Medical Agent, Emergency Agent, Tourism Agent | Hospital admin / data import |
| `appointments` | Both the doctor's available slots and confirmed patient bookings in one table. A `patient_id` column is null for open slots and populated once a patient books. A `status` column tracks: `available`, `booked`, `cancelled`, `blocked` | Booking Agent, Medical Agent (availability check), Emergency Agent (on-call check), CRM Agent | Booking Agent only |
| `complaints` | Complaint tickets: category, priority, status, SLA deadline, resolution | Complaint Agent | Complaint Agent |
| `kb_chunks` | All knowledge base content — medical articles, emergency first-aid rules, and tourism packages — in one table. A `domain` column (`medical` / `emergency` / `tourism`) scopes every search to the right content. Each row carries an embedding for semantic search | Medical RAG Agent, Emergency Agent, Tourism Agent | Quarterly/monthly offline refresh processes |
| `loyalty` | One row per patient for current tier, points balance, and visit count; plus one append-only row per transaction (point award or redemption) distinguished by a `record_type` column (`account` / `transaction`). The agent reads the `account` row for current state and appends `transaction` rows for history — no separate table needed | Loyalty Agent | Loyalty Agent |
| `staff_queue` | A single table for everything that needs a human to act on: emergency escalations and payment/billing requests. A `type` column (`emergency` / `payment`) tells the staff dashboard which queue it belongs to. Keeping them together means one place to monitor SLA and one schema to maintain | Human staff dashboard, billing staff | Emergency Agent (emergency rows); Orchestrator (payment rows) |
| `session_state` | Mid-conversation flags (verification status, mid-booking indicator, etc.) plus a `conversation_summary` text column written by the Orchestrator at session end — a human-readable paragraph of what happened, what was resolved, and any open items. Replaces the old `interaction_logs` table | Orchestrator, all agents | Orchestrator, all agents |
| *(SDK-managed)* `agent_sessions` / `agent_messages` | Full conversation transcripts, created and managed automatically by the Agents SDK's session feature | Agents SDK runtime (for memory continuity) | Agents SDK runtime |

**Access model, in one sentence per data type:** the Booking & Doctor Agent is the only agent that ever writes to `appointments`; every other agent that needs doctor or availability data only reads it. The Loyalty Agent only reads patient identity from `patients` and only writes to `loyalty`. The Orchestrator is the only agent that writes payment rows to `staff_queue`; the Emergency Agent is the only agent that writes emergency rows to the same table.

---

## 3. Expected User Load (capacity planning)

These are **planning assumptions for the MVP**, not measured numbers — they should be replaced with Cleopatra Hospital's actual patient volume before sizing infrastructure. They're included here so the database and deployment choices in this plan are made against a concrete target rather than left vague.

| Tier | Assumption | Why it matters |
|---|---|---|
| Registered patient base | A few thousand to low tens of thousands of patients in the CRM at MVP launch | Affects index sizing on `patients`/`appointments`, not a real constraint at Postgres scale |
| Concurrent active conversations | Tens to low hundreds at any given moment (single hospital, MVP channels only) | Determines the database connection pool size and whether a single Postgres instance (vs. read replicas) is sufficient — it is, at this tier |
| Daily messages handled | Low thousands per day across web/WhatsApp during MVP | `pgvector` with an `hnsw` index comfortably serves this; no caching layer is required yet |
| Knowledge base size | A few thousand to low tens of thousands of content chunks across all specialties + emergency + tourism | Vector search stays fast at this size without a dedicated vector database |
| Emergency escalations | Expected to be a small fraction of total volume, but **must never queue or degrade**, regardless of overall load | This is why the Emergency Agent uses the stronger model and writes directly to `staff_queue` rather than sharing any routine traffic path |

**Scaling note:** the single-Postgres design is intentionally sized for "one hospital's MVP traffic," not "national rollout." If patient volume or concurrency grows by an order of magnitude, the first additions would be a read replica for the heavier read paths (doctor search, knowledge base queries) and a caching layer in front of session state — both additive changes, not architecture rewrites.

---

## 4. Framework — OpenAI Agents SDK

The OpenAI Agents SDK (Python package `openai-agents`) is the orchestration layer. It provides five building blocks used throughout this plan:

- **Agents** — an LLM configured with instructions, a model, and a set of tools it's allowed to call. Each specialist in this plan (CRM, Booking, Complaint, etc.) is one Agent.
- **Tools** — typed functions an Agent can call to read or write data. The LLM never touches the database directly; it only sees what a tool returns.
- **Handoffs** — the mechanism by which one Agent transfers an ongoing conversation to another Agent (e.g. the Orchestrator handing a booking question to the Booking & Doctor Agent). The patient experiences this as a single continuous conversation, not a transfer.
- **Guardrails** — checks that run alongside an Agent to catch things like emergency or payment intent early, without necessarily blocking the conversation.
- **Sessions** — automatic conversation memory, so the patient never has to repeat themselves within (or, with persistent storage, across) a conversation. This is the feature that lets the MVP store conversation history in Postgres instead of needing Redis.

The SDK also includes built-in tracing, which gives visibility into every agent call, tool call, and handoff for debugging and quality review — useful for an MVP where routing accuracy needs to be tuned based on real conversations.

---

## 5. OpenAI Models

| Use case | Model | Reasoning |
|---|---|---|
| Orchestrator (Triage Agent) | Stronger reasoning model | Routing accuracy is the single biggest driver of whether the whole system feels coherent; under-routing here cascades into every other agent |
| Emergency Agent | Stronger reasoning model | Safety-critical — this is the one agent where a wrong call has real consequences, so it gets the same tier as the Orchestrator regardless of cost |
| CRM, Booking & Doctor, Complaint, Medical RAG, Medical Tourism, Loyalty & Retention Agents | Smaller/faster, cost-efficient model | These are largely structured, tool-driven tasks (lookups, CRUD-style actions, grounded Q&A) that don't need the most expensive model to perform reliably |
| Intent signal detector (used by the emergency/payment guardrail) | Smaller, fast model | A focused yes/no classification task running on every incoming message — needs to be cheap and fast, not deeply reasoning |
| Embeddings (for all knowledge-base search) | OpenAI's small embedding model | Lowest-cost tier that performs well for medical FAQ-style retrieval at MVP scale; can be upgraded to a larger embedding model later without changing anything except re-embedding existing content |

This two-tier model strategy (strong model only where routing/safety is at stake, efficient model everywhere else) keeps per-conversation cost low while not compromising on the parts of the system where mistakes matter most.

---

## 6. Agents

### 6.1 Orchestrator (Triage Agent) — *root agent*
**Role:** entry point for every conversation. Determines intent and routes to the right specialist; does not answer medical, booking, or complaint questions itself.
**Touches:** `staff_queue` (payment rows only); writes `conversation_summary` to `session_state` at session end.
**Key behavior:** new/unclear conversations route to the CRM Agent first to resolve identity; anything that sounds like a medical emergency routes to the Emergency Agent immediately, even before identity is confirmed; payment, billing, invoice, and refund requests are never handed to another agent — the Orchestrator queues them for a human directly.

### 6.2 CRM Agent
**Role:** resolves patient identity and serves patient profile context to every other agent.
**Touches:** `patients` (read/write), `session_state` (reads `conversation_summary` for returning patients).
**Key behavior:** never returns profile data before identity is verified by phone number and date of birth; stores no clinical diagnosis data, only non-clinical CRM notes; every access is logged.

### 6.3 Booking & Doctor Agent
**Role:** the only agent that books, reschedules, or cancels appointments. Also the source of truth for doctor profiles and per-doctor pre-visit requirements.
**Touches:** `doctors` (read), `appointments` (read/write).
**Key behavior:** refuses to book without a verified patient; always surfaces referral/document requirements alongside availability; if asked a medical question instead of a booking question, hands off to the Medical RAG Agent; checks with the Loyalty Agent first if the patient mentions a discount or priority slot.

### 6.4 Complaint Agent
**Role:** logs and tracks complaint tickets end-to-end, including SLA-based escalation.
**Touches:** `complaints` (read/write).
**Key behavior:** assigns priority honestly (critical means safety-adjacent, not just frustration); always gives the patient a ticket number; critical-priority complaints trigger immediate escalation rather than waiting on the normal SLA clock.

### 6.5 Medical RAG Agent — *covers all 11 specialties*
**Role:** answers non-urgent medical, disease, and hospital-service questions across every specialty (General Medicine, Cardiology, Orthopedics, Dermatology, Pediatrics, Gynecology & Obstetrics, Neurology, Oncology, ENT, Ophthalmology, Psychiatry).
**Touches:** `kb_chunks` (read, filtered by `domain = 'medical'` and specialty), `doctors` and `appointments` (read-only, for "which doctor handles this").

**Key behavior:** always grounds answers in retrieved knowledge-base content; never diagnoses; immediately hands off to the Emergency Agent if symptoms described sound urgent; never books — only the Booking & Doctor Agent does that.

### 6.6 Emergency Agent
**Role:** triages potentially urgent symptoms, gives first-aid guidance, and escalates to human staff.
**Touches:** `kb_chunks` (read, `domain = 'emergency'`), `doctors` (read, for on-call lookup), `staff_queue` (write, emergency rows).
**Key behavior:** classifies into Critical / Urgent / Non-urgent; Critical cases get an immediate "call emergency services or go to the ER" instruction plus a human alert, without waiting to finish gathering details; never diagnoses, always includes a disclaimer; Non-urgent cases get redirected to the Medical RAG Agent or Booking & Doctor Agent for a routine appointment.

### 6.7 Medical Tourism Agent
**Role:** supports international patients with treatment packages, logistics, and travel-related information.
**Touches:** `kb_chunks` (read, `domain = 'tourism'`).
**Key behavior:** gives general pricing tiers only, never exact invoice amounts; hands off to Booking & Doctor Agent for scheduling and CRM Agent for identity; supports both Arabic and English.

### 6.8 Loyalty & Retention Agent
**Role:** tracks loyalty tier, points, and perks; coordinates discounts with booking and tourism.
**Touches:** `loyalty` (read/write), `patients` (read-only for identity; sets `reengagement_flagged = true` for inactive high-value patients).
**Key behavior:** always confirms identity via CRM first; never modifies clinical or contact data, only loyalty data; treats point redemption toward a payment as a payment-adjacent request and routes it to a human rather than processing it.

### 6.9 Payment / Billing — *not an agent*
**Role:** any payment, billing, invoice, or refund request is detected by the Orchestrator and placed directly into `staff_queue` for a human staff member. No AI agent ever processes a financial transaction.

---

## 7. Tools

Each agent's tools are the only way it touches the database — the model never runs raw queries itself.

### CRM Agent
| Tool | What it does |
|---|---|
| Verify identity | Confirms a patient's identity using phone number and date of birth; on success, marks the session as verified |
| Get patient profile | Returns the verified patient's contact info, preferences, and the last conversation summary — refuses if not yet verified |
| Update patient preferences | Updates language and preferred communication channel |

### Booking & Doctor Agent
| Tool | What it does |
|---|---|
| Search doctors | Finds doctors by specialty and optional name, including rating, location, and requirements |
| Check slots | Lists available appointment rows for a doctor within a date range |
| Book appointment | Sets a slot row to `booked` and assigns the verified patient; fails safely if the slot was already taken in the meantime |
| Reschedule appointment | Moves an existing booking to a different available slot |
| Cancel appointment | Sets the booking to `cancelled` and clears `patient_id`, freeing the slot |
| Get doctor requirements | Returns a doctor's referral, test, and document requirements |

### Complaint Agent
| Tool | What it does |
|---|---|
| Create complaint | Files a new complaint with an auto-generated ticket number and an SLA deadline based on priority |
| Get complaint status | Looks up a complaint's current status by ticket number |
| Escalate complaint | Escalates a complaint that has breached or is about to breach its SLA |
| Close complaint | Closes a resolved complaint and records a satisfaction rating |

### Medical RAG Agent
| Tool | What it does |
|---|---|
| Search knowledge base | Semantic search over `kb_chunks` scoped to `domain = 'medical'` and the relevant specialty |
| Check doctor availability | Read-only lookup of doctors and their next available slot in a specialty — does not book |

### Emergency Agent
| Tool | What it does |
|---|---|
| Get first-aid guidance | Semantic search over `kb_chunks` (`domain = 'emergency'`) for the described symptoms, including urgency classification |
| Get on-call doctors | Read-only lookup of on-call/ER doctors, optionally filtered by specialty |
| Escalate to human | Writes an emergency row to `staff_queue` for staff to act on immediately |

### Medical Tourism Agent
| Tool | What it does |
|---|---|
| Search packages | Semantic search over `kb_chunks` (`domain = 'tourism'`), optionally filtered by specialty |
| Get package details | Returns full details for a specific package — pricing tier and logistics, not exact billing |
| Request coordinator | Writes a coordinator-request note so a human tourism coordinator can follow up |

### Loyalty & Retention Agent
| Tool | What it does |
|---|---|
| Get loyalty profile | Returns the patient's tier, points balance, and visit count from the `account` row; creates one if it doesn't exist yet |
| Award points | Appends a `transaction` row for a completed appointment, referral, or review, and updates the `account` balance |
| Apply booking discount | Returns the patient's tier-based discount percentage for the Booking Agent to apply |
| Flag re-engagement | Sets `reengagement_flagged = true` on the patient row for the marketing follow-up workflow |

### Orchestrator (Triage Agent)
| Tool | What it does |
|---|---|
| Escalate to payment queue | Writes a payment row to `staff_queue` for a human billing agent |
| Write conversation summary | At session end, writes a short text paragraph into `session_state.conversation_summary` — what the patient needed, what was done, and any open items |

---

## 8. How It Comes Together (no code, just the flow)

A patient message arrives from any channel and reaches the Orchestrator first. The Orchestrator reads the session's current state (is this patient verified yet? mid-booking? recently flagged as an emergency?) and decides where the conversation should go. If the message reads as a medical emergency, it routes straight to the Emergency Agent, even before identity is confirmed. If it reads as a payment question, the Orchestrator writes a row to `staff_queue` directly, with no further routing. Everything else routes to the relevant specialist, which may hand the conversation off again later in the same turn — most commonly, the Medical RAG Agent or the Medical Tourism Agent handing off to the Booking & Doctor Agent once the patient decides to actually schedule something.

Every specialist agent shares the same patient and session context, so nothing needs to be re-asked once it's known. The full conversation is saved automatically after every turn by the SDK. When the session ends, the Orchestrator writes a one-paragraph summary into `session_state` so the CRM Agent can greet the patient with context on their next visit. Emergency escalations and payment requests each land in `staff_queue` so staff dashboards pick them up without parsing transcripts.

---

## 9. Deployment

### 9.1 Services and Their Roles

**FastAPI application server** — the Python process running the OpenAI Agents SDK. It receives the patient message, instantiates the correct session, runs the Orchestrator, and returns the agent's reply. For the MVP, one or two instances behind a load balancer are sufficient at the expected concurrency level described in Section 3. The application is containerized (Docker) so it can be scaled horizontally without any code changes if load increases.

**PostgreSQL (managed)** — the single database described in Sections 1 and 2. For the MVP, a managed Postgres service (e.g. Amazon RDS, Cloud SQL, Azure Database for PostgreSQL) is strongly preferred over a self-hosted instance: automated backups, point-in-time recovery, and minor-version patching are handled by the provider, not the team. The `pgvector` extension must be enabled on the instance at creation time. One instance with moderate compute (e.g. 2–4 vCPUs, 8–16 GB RAM) covers the MVP load; a read replica can be added later for the heavier read paths without changing any application code.

**API Gateway / reverse proxy** — sits in front of the FastAPI server, handles TLS termination, rate limiting (per IP and per patient session), and authentication token validation. NGINX or a managed gateway service (AWS API Gateway, Cloud Endpoints) both work. This layer is the single point where inbound traffic is validated before it reaches the application.

### 9.2 Secrets and Configuration

All secrets (OpenAI API key, database connection string, Meta WhatsApp token) are stored in a secrets manager (AWS Secrets Manager, GCP Secret Manager, or Azure Key Vault) and injected into the application as environment variables at startup. No secret appears in source code, Docker images, or repository history.

Application-level configuration (model names, SLA thresholds, knowledge-base refresh schedule) is stored in a `.env` file per environment (`dev`, `staging`, `production`) and loaded at startup. Changing a model name or SLA threshold requires a config change and a service restart, not a code change.

### 9.3 Observability

**Logging:** every inbound message, agent handoff, tool call, and outbound reply is logged with the session ID and a timestamp. Logs are shipped to a log aggregation service (CloudWatch, Datadog, or similar). PII fields (patient phone, date of birth) are redacted from logs at the application layer before shipping.

**Tracing:** the OpenAI Agents SDK provides built-in trace data for every agent run — which agent was called, which tools fired, how long each step took, and what the handoff chain looked like. These traces are stored in the SDK's trace store (or exported to the log aggregator) and are the primary tool for debugging routing errors during the MVP tuning period.

**Alerting:** three alert thresholds are configured from day one: (1) any unhandled exception in the FastAPI application; (2) any emergency escalation row written to `staff_queue` that is not acknowledged within five minutes; (3) database CPU or connection count exceeding 80% of capacity. Alerts go to the on-call engineer via the hospital's existing notification channel (email, PagerDuty, Slack, etc.).


---

## 10. Prompt Engineering Framework

Every agent in the system has a system prompt that defines its identity, its scope, its constraints, and its handoff rules. Rather than writing these freeform, all prompts follow a shared five-section template. This makes prompts consistent across agents, easier to review, and easier to update when behavior needs to change.

### 10.1 The Five-Section Prompt Template

**Section 1 — Identity and Role**
One or two sentences establishing who the agent is and what it is responsible for. The language is declarative and first-person: "You are the Booking & Doctor Agent for Cleopatra Hospital. Your sole responsibility is to help verified patients find doctors, check availability, and manage appointments."

This section must be specific enough that the agent would refuse a task outside its scope without being told explicitly. An agent whose identity is "I answer everything" will drift; an agent whose identity is "I book appointments" will stay in lane.

**Section 2 — What You Have Access To**
An explicit list of the tools available to this agent, with a one-line description of what each tool does. The model cannot hallucinate a tool call if it knows exactly what its toolset is. This section also notes what the agent cannot see — for example, the Booking Agent's prompt states that it does not have access to the patient's loyalty tier directly and must ask the Loyalty Agent.

**Section 3 — Behavioral Rules**
A numbered list of constraints the agent must follow unconditionally. These are not suggestions — they are guardrails written in imperative language ("Never book an appointment without a verified session. Never answer a medical question — hand off to the Medical RAG Agent instead."). Rules are kept short and binary: either the agent does the thing or it doesn't.

The most important behavioral rules for each agent are:
- **Orchestrator:** never answer content questions; never process payments; route emergencies before identity verification.
- **CRM Agent:** never return profile data before identity is verified; never store diagnosis or clinical data.
- **Booking Agent:** never book without a verified session; always surface doctor requirements before confirming a slot.
- **Medical RAG Agent:** never diagnose; never book; always cite the retrieved knowledge-base chunk as the source of the answer.
- **Emergency Agent:** never withhold a "call emergency services" instruction for Critical cases regardless of how much additional information would be useful to gather first.
- **All agents:** never make up information that is not in the retrieved data or the patient's verified profile.

**Section 4 — Handoff Conditions**
An explicit list of the conditions under which this agent hands the conversation to another agent, and which agent it hands to. Handoffs are named explicitly: "If the patient asks to book an appointment, hand off to the Booking & Doctor Agent. If the patient describes symptoms that sound urgent, hand off to the Emergency Agent immediately."

This section prevents agents from trying to complete tasks that belong to another agent. A common failure mode in multi-agent systems is an agent that is "almost capable" of doing something and tries to do it rather than handing off. Explicit handoff conditions, listed in the prompt and reinforced by the SDK's handoff mechanism, prevent this.

**Section 5 — Response Style**
Brief guidance on tone, length, and language. All patient-facing agents follow the same baseline: warm but professional; Arabic or English depending on the patient's detected or stated preference; never more than three sentences for a simple acknowledgment; structured (step-by-step or bulleted) for multi-part answers like appointment details or first-aid instructions.

The Emergency Agent has an additional style rule: urgency classifications (Critical / Urgent / Non-urgent) are always stated explicitly and early in the response, never buried.

### 10.2 Prompt Storage and Versioning

System prompts are stored as plain-text files in the repository under `prompts/agents/`. Each file is named after the agent (`orchestrator.txt`, `crm_agent.txt`, etc.). Prompts are loaded at application startup and injected into each Agent's configuration — they are not hardcoded in Python. This means a prompt change is a file edit and a service restart, not a code change.

Every prompt file includes a header comment with its version number and the date it was last changed. When a prompt is updated, the old version is kept in `prompts/history/` with the version number appended to the filename. This makes it possible to roll back a prompt change without rolling back code.

### 10.3 Few-Shot Examples

For agents where the expected response format is non-obvious — particularly the Orchestrator's routing decisions and the Emergency Agent's triage classifications — the system prompt includes three to five few-shot examples in the form of `[Patient message] → [Expected agent action]`. These examples are not conversations; they are compact routing demonstrations. They are stored in the same file as the system prompt, after the five sections, under a clearly marked `## Examples` header.

### 10.4 Guardrail Prompts

The emergency/payment intent detector (described in Section 5) has its own minimal prompt: a classification instruction, a list of signal phrases for each intent type (emergency vs. payment), and an instruction to return a single JSON object with fields `emergency: true/false` and `payment: true/false`. This prompt is stored separately at `prompts/guardrails/intent_detector.txt` and follows the same versioning convention.

---

## 11. Project Folder Structure

The repository contains all application code, prompts, database migrations, deployment configuration, and background job scripts in a single monorepo. The structure below is the target state at the end of Phase 5 (MVP complete).

```
cleopatra-patient-assistant/
│
├── app/                          # FastAPI application
│   ├── main.py                   # App entry point; registers routes and lifespan events
│   ├── config.py                 # Loads environment variables and app-level settings
│   │
│   ├── agents/                   # One file per agent
│   │   ├── orchestrator.py       # Triage Agent — entry point, routing, payment escalation
│   │   ├── crm_agent.py          # CRM Agent — identity verification, patient profile
│   │   ├── booking_agent.py      # Booking & Doctor Agent — slots, bookings, doctor search
│   │   ├── complaint_agent.py    # Complaint Agent — tickets, SLA tracking
│   │   ├── medical_rag_agent.py  # Medical RAG Agent — grounded Q&A across specialties
│   │   ├── emergency_agent.py    # Emergency Agent — triage, first aid, escalation
│   │   ├── tourism_agent.py      # Medical Tourism Agent — packages, coordinator requests
│   │   └── loyalty_agent.py      # Loyalty & Retention Agent — points, tiers, discounts
│   │
│   ├── tools/                    # One file per agent's toolset
│   │   ├── crm_tools.py
│   │   ├── booking_tools.py
│   │   ├── complaint_tools.py
│   │   ├── medical_rag_tools.py
│   │   ├── emergency_tools.py
│   │   ├── tourism_tools.py
│   │   ├── loyalty_tools.py
│   │   └── orchestrator_tools.py
│   │
│   ├── guardrails/               # Guardrail logic
│   │   └── intent_detector.py    # Emergency/payment intent classifier (runs on every message)
│   │
│   ├── db/                       # Database layer
│   │   ├── connection.py         # Connection pool setup
│   │   ├── session_store.py      # SDK session persistence adapter for Postgres
│   │   └── queries/              # One file of typed query functions per table
│   │       ├── patients.py
│   │       ├── doctors.py
│   │       ├── appointments.py
│   │       ├── complaints.py
│   │       ├── kb_chunks.py
│   │       ├── loyalty.py
│   │       ├── staff_queue.py
│   │       └── session_state.py
│   │
│   ├── channels/                 # Channel adapters
│   │   ├── whatsapp_webhook.py   # Receives and normalizes WhatsApp messages
│   │   └── web_chat.py           # Web chat widget endpoint
│   │
│   └── schemas/                  # Pydantic models for request/response validation
│       ├── messages.py
│       ├── patients.py
│       ├── appointments.py
│       └── staff_queue.py
│
├── prompts/                      # All system prompts — no prompt strings in Python files
│   ├── agents/
│   │   ├── orchestrator.txt
│   │   ├── crm_agent.txt
│   │   ├── booking_agent.txt
│   │   ├── complaint_agent.txt
│   │   ├── medical_rag_agent.txt
│   │   ├── emergency_agent.txt
│   │   ├── tourism_agent.txt
│   │   └── loyalty_agent.txt
│   ├── guardrails/
│   │   └── intent_detector.txt
│   └── history/                  # Previous prompt versions — named with version suffix
│       └── orchestrator_v1.txt
│
├── jobs/                         # Background / scheduled tasks
│   ├── kb_refresh.py             # Re-embeds updated knowledge-base content into kb_chunks
│   └── sla_monitor.py            # Checks complaint SLA deadlines; triggers escalation tool
│
├── deploy/                       # Deployment and infrastructure configuration
│   ├── Dockerfile                # Production container image
│   ├── docker-compose.dev.yml    # Local dev stack (FastAPI + Postgres with pgvector)
│   ├── nginx.conf                # Reverse proxy / rate limiting configuration
│   └── k8s/                      # Kubernetes manifests (if deploying to a cluster)
│       ├── deployment.yaml
│       ├── service.yaml
│       └── configmap.yaml
│
├── .env.dev                      # Dev environment variables (never committed with real secrets)
├── .env.staging                  # Staging environment variables
├── .env.production               # Production environment variables (populated by secrets manager)
├── .gitignore
├── pyproject.toml                # Dependencies (managed with Poetry or pip-tools)
├── alembic.ini                   # Alembic migration configuration
└── README.md                     # Setup, local dev instructions, environment variable reference
```

**Key structural decisions:**
- Prompts live in `prompts/`, not in Python files, so a prompt change never requires a code review.
- Each agent and each agent's toolset are in separate files — this keeps individual files short and makes it easy to assign one agent to one developer during the build phases.
- The `db/queries/` layer contains only database access functions — no business logic. Agents call tools; tools call query functions; query functions call the database. This three-layer separation makes it possible to unit-test tools with a mock query layer.
- `deploy/docker-compose.dev.yml` spins up the full local stack — FastAPI and Postgres with pgvector — with a single command, so a new developer can run the system locally without installing Postgres manually.

---

## 12. Roadmap Snapshot

| Phase | Focus |
|---|---|
| 1 | Database live; FastAPI skeleton; CRM Agent working end-to-end |
| 2 | Booking & Doctor Agent, Complaint Agent, Orchestrator routing, payment handoff |
| 3 | Knowledge base populated + Medical RAG Agent; Emergency Agent |
| 4 | Loyalty & Retention Agent, Medical Tourism Agent |
| 5 | Background cleanup jobs, monitoring, one live channel |

Roughly an 8-week MVP, compared to the original 20-week plan — the time saved comes from consolidating to one database and one Medical Agent instead of eleven, not from cutting any patient-facing capability.
