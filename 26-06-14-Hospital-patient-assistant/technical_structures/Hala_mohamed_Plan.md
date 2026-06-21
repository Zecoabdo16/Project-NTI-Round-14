## 5. Granular Multi-Agent Breakdown & Operational Flow

### 🤖 1. Call Optimization & Router Agent
* **LLM Engine:** `gpt-4o-mini` (Optimized for speed and minimal token cost).
* **Operational Objective:** Act as the asynchronous gatekeeper to classify, route, and deflect traffic incoming from system webhooks (WhatsApp/Voice/Web).
* **Step-by-Step Execution Flow:**
  1. Ingests the initial raw user payload (text message or voice transcript).
  2. Runs a high-speed system prompt classification matrix to evaluate user intent.
  3. Checks system environment flags: If incoming traffic is via a voice call and the wait time queue exceeds SLA thresholds, it triggers the text deflection sub-routine.
  4. Updates the LangGraph shared `State` object with the identified intent and routes the state to the corresponding specialized worker node.
* **Assigned Tools (`app/tools/`):**
  * `telecom_deflection_webhook`: Fires an outbound API call to the telecom provider to initiate the IVR-to-WhatsApp session transition.
  * `intent_classifier_filter`: A lightweight deterministic prompt tool to enforce hard routing categories.

---

### 🩺 2. Patient History & Smart Intake Agent
* **LLM Engine:** `Claude 3.5 Sonnet` or `GPT-4o` (Selected for deep medical reasoning and complex structural extraction).
* **Operational Objective:** Build a structured, multi-dimensional medical profile (SOAP note) from raw, unorganized multi-modal data streams.
* **Step-by-Step Execution Flow:**
  1. Receives the user data bundle from the Router Agent (can contain text, prescription photos, or audio voice memos)[cite: 2].
  2. Executes parallel asynchronous peripheral tool calls: fires Whisper for voice transcription and Vision LLM for handwriting/prescription OCR[cite: 2].
  3. Queries the `Neo4j` database using the patient's family surname to pull genetic health charts (Family Genogram)[cite: 2].
  4. Synthesizes the transcribed text, OCR data, and family risk data into a clinically structured JSON object mapping directly to a standard medical **SOAP Note** (Subjective, Objective, Assessment, Plan)[cite: 2].
  5. Pushes the generated schema to the Doctor Dashboard via WebSockets for manual verification (Human-in-the-Loop gatekeeper protocol)[cite: 2].
* **Assigned Tools (`app/tools/`):**
  * `medical_ocr`: Utilizes Vision LLM capabilities to parse handwritten or printed prescriptions and lab reports into text[cite: 2].
  * `voice_transcribe`: Wraps the OpenAI Whisper API to ingest raw audio binary and output structured text strings[cite: 2].
  * `neo4j_client`: Builds dynamic Cypher queries to navigate and fetch nodes from the genetic family graph[cite: 2].

---

### 🚨 3. Emergency Bypass Guardrail (Safety Engine)
* **LLM Engine:** Hard-coded Deterministic Regex/Token Matrices + Fine-tuned Binary LLM Classifier.
* **Operational Objective:** Act as a zero-latency safety firewall to intercept life-threatening symptoms and bypass all AI reasoning to ensure immediate human/ambulance dispatch[cite: 2].
* **Step-by-Step Execution Flow:**
  1. Evaluates incoming user inputs in parallel with the Router Agent using a hard-coded red-flag token directory (e.g., "chest pain", "severe bleeding", "unconscious").
  2. If a red-flag condition matches, it completely intercepts the LangGraph pipeline execution, shifting the system state to `CRITICAL_EMERGENCY`.
  3. Instantly queries location-gathering APIs to pin down user telemetry or pushes an urgent prompt asking for immediate location data.
  4. Opens an active WebSocket connection to fire visual and audible alarms directly on the ER Nurse Console.
* **Assigned Tools (`app/tools/`):**
  * `gps_locator_api`: Resolves available network/device telemetry into geocoding points.
  * `er_console_websocket_pusher`: Streams instant HTTP/WebSocket alerts to trigger red flashing dashboard UI updates on the medical staff's end[cite: 2].
  * `synthetic_voice_outbound`: Initiates a backup automated outbound call to the ER emergency supervisor line if WebSocket latency degrades.

---

## 6. Comprehensive Database Architecture & Handling

To handle relational logs, semantic documentation, and highly connected clinical relationships, HAOS implements a **Tri-Database Architecture** layer managed within `app/database/`[cite: 2].

```mermaid
graph TD
    subgraph Data Ingestion Layer
        A[Incoming Unified System State]
    end
    subgraph Storage Allocation Matrix
        A -->|Clinical Records & Operational Logs| B[(PostgreSQL DB)]
        A -->|Hospital Policies & Insurance Docs| C[(ChromaDB / Pinecone)]
        A -->|Family Lineage & Inheritable Risks| D[(Neo4j Graph Database)]
    end
1. Relational Layer: PostgreSQL (Audit Ledger & Core Patient Metadata)
Purpose: Acts as the single point of truth for permanent patient records, transactional operation logs, and audit trails required for medical regulatory compliance[cite: 2].

Schema Blueprint (SQLAlchemy / Pydantic Definitions):
# app/database/schemas.py
  from datetime import datetime
  from pydantic import BaseModel
  from typing import Optional, Dict

  class PatientMetadata(BaseModel):
      patient_id: str
      full_legal_name: str
      date_of_birth: datetime
      gender: str
      phone_number: str
      created_at: datetime

  class SystemAuditTrail(BaseModel):
      log_id: str
      patient_id: str
      agent_identity: str  # ['ROUTER', 'INTAKE', 'EMERGENCY']
      raw_input_payload: str
      generated_soap_note: Optional[Dict] = None
      doctor_approved: bool = False
      timestamp: datetime
🧠 2. Knowledge Graph Layer: Neo4j (GraphRAG for Family Medical Genograms)
Purpose: Maps biological connections and hereditary disease transmissions across generations to discover underlying clinical risk factors automatically[cite: 2].

Node & Relationship Data Structure:

Nodes:

(:Patient {id: "P101", name: "Hala"})

[cite: 2]

(:Disease {code: "ICD-10-I21", name: "Myocardial Infarction"})

Relationships:

(:Patient)-[:BIOLOGICAL_PARENT_OF]->(:Patient)

(:Patient)-[:DIAGNOSED_WITH {age_at_onset: 50}]->(:Disease)

Cypher Query Example (Executed by neo4j_client.py):
// Look up if any biological ancestor had hereditary heart conditions
  MATCH (p:Patient {id: $current_patient_id})-[:BIOLOGICAL_PARENT_OF*1..3]->(ancestor:Patient)
  MATCH (ancestor)-[r:DIAGNOSED_WITH]->(d:Disease {name: "Myocardial Infarction"})
  RETURN ancestor.name, d.name, r.age_at_onset
3. Vector Database Layer: ChromaDB / Pinecone (Administrative FAQ & Insurance RAG)
Purpose: Stores and queries highly detailed chunks of text regarding hospital procedures, coverage limitations, and insurance frameworks via dense vector semantic lookups[cite: 2].

Data Ingestion Pipeline:

Ingests raw PDFs (Hospital rulebooks, Insurance contract clauses).

Splits text into 500-token semantic chunks with a 50-token overlap strategy.

Generates dense vector representations utilizing the text-embedding-3-small engine.

Persists embeddings inside collection spaces indexed for Cosine Similarity lookups.

Vector Metadata Payload Schema:
{
    "id": "doc_chunk_842",
    "vector": [0.012, -0.043, 0.231, "..."],
    "metadata": {
      "document_type": "Insurance_Policy",
      "carrier_name": "AXA_Healthcare",
      "clause_category": "Pre_Existing_Conditions",
      "raw_text_chunk": "Section 4.2: Coverage details regarding chronic heart failures and genetic predispositions..."
    }
  }