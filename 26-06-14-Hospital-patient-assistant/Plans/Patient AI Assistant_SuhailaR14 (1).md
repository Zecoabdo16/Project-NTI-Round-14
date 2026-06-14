## **Patient AI Assistant**

##             ***A 24/7 Digital Front Door for the Hospital* (Business Proposal)** 

Hospitals lose time, money, and patient trust to a problem that is largely **administrative**: phone lines are jammed, receptionists repeat the same questions, clinicians lack context when patients call, and there is no consistent way to determine who needs help first.

The **Patient AI Assistant** is a 24/7 intelligent front door that answers calls and chats, remembers every patient, routes them to the right resource, and flags emergencies in seconds. It works alongside staff *— not in place of them —* and is designed to deliver measurable savings within the first year of deployment.

## **1\. The Problem**

Hospitals face the same five frustrations every day. None of them require new medicine to solve; they require better **coordination**.

### **1.1 Wasted Time**

* Patients repeat the same information to every person they speak with.  
* Receptionists spend 40 – 60% of their day on questions that do not need a human.  
* Clinicians enter visits without context, so the first 3–5 minutes are spent catching up.

### **1.2 Limited Availability**

* Phone lines are closed at night and on weekends.  
* Booking the right specialist can take multiple callbacks.  
* Emergency room capacity is invisible to patients until they arrive.

### **1.3 Long Call Times**

* Average wait to reach a human: 4 – 12 minutes during peak hours.  
* 20 – 30% of callers abandon before being answered.  
* Each abandoned call is a lost visit and a frustrated patient.

### **1.4 No Continuity**

* Every call starts from zero.  
* Clinicians do not remember a patient they saw 3 months ago.  
* Follow-ups depend on the patient remembering to call back.

### 

### **1.5 No Prioritization**

* Calls are answered in the order they arrive.  
* A chest-pain patient may wait behind a prescription refill.  
* Risk is identified too late.

## **2\. The Solution and Who It Serves**
flowchart TB
    AI[Patient AI Assistant<br/>Always-on, multilingual,<br/>remembers everything]

    AI -->|Faster answers,<br/>no repetition,<br/>24/7 access| P[Patients]
    AI -->|Fewer routine calls,<br/>focus on in-person care| R[Reception Staff]
    AI -->|Patient summary<br/>before they join| C[Clinicians<br/>Nurses + GPs]
    AI -->|Early warning,<br/>pre-arrival context| E[Emergency Team]
    AI -->|Live dashboards,<br/>measurable ROI,<br/>capacity insight| M[Hospital Management]
    AI -->|Audit logs,<br/>consent controls,<br/>compliance reports| IT[IT & Compliance]

    P -->|Loyalty,<br/>better reviews| H[Hospital]
    R -->|Lower workload,<br/>higher morale| H
    C -->|More time for care| H
    E -->|Better outcomes| H
    M -->|Lower cost,<br/>higher revenue| H
    IT -->|Lower risk| H

    classDef system fill:#fff3e0,stroke:#e65100,color:#bf360c
    classDef user fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef org fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20

    class AI system
    class P,R,C,E,M,IT user
    class H org

## **3\. Patient Journey**

flowchart LR
    A[Patient<br/>calls, chats, opens app] --> B{New or<br/>returning?}
    B -- Returning --> C[Greeted by name<br/>History loaded<br/>(History Agent)]
    B -- New --> D[Quick 30-sec<br/>registration<br/>(Comm Agent)]
    C --> E[Understands need<br/>in plain language<br/>(Comm Agent)]
    D --> E
    E --> F{Need type?}
    F -- Routine --> G[Books slot or<br/>answers question<br/>(Scheduling Agent)]
    F -- Medical --> H[Asks symptom<br/>questions<br/>(Triage Agent)]
    F -- Emergency --> I[Pages clinician<br/>in under 30 sec<br/>(Escalation Agent)]
    H --> J{Risk level}
    J -- Low --> K[Self-care advice<br/>(Triage Agent)]
    J -- Medium --> L[Same-day<br/>appointment booked<br/>(Scheduling Agent)]
    J -- High --> I
    I --> M[Clinician joins<br/>with full patient context<br/>(Escalation Agent)]
    K --> N[Confirmation +<br/>follow-up reminder<br/>(Comm Agent)]
    G --> N
    L --> N
    M --> N
    N --> O[Satisfied patient<br/>+ audit log captured]

    %% --- Agent color classes ---
    classDef comm fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef hist fill:#f3e5f5,stroke:#6a1b9a,color:#4a148c
    classDef triage fill:#fff3e0,stroke:#e65100,color:#bf360c
    classDef sched fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef esc fill:#ffebee,stroke:#c62828,color:#b71c1c
    classDef decision fill:#fffde7,stroke:#f9a825,color:#f57f17
    classDef outcome fill:#fafafa,stroke:#616161,color:#212121

    class A,O outcome
    class B,F,J decision
    class D,E,N comm
    class C hist
    class H,K triage
    class G,L sched
    class I,M esc

## **4\. Data Requirements**

### **4.1 Data Types**

| Category | Examples | Source |
| ----- | ----- | ----- |
| Patient demographics | Age, sex, language, contact | Hospital registration |
| Clinical history | Diagnoses, meds, allergies, prior visits | EHR / mock dataset |
| Current encounter | Symptoms, vitals, chief complaint | Patient self-report \+ devices |
| Resource data | Doctor schedules, room status, on-call roster | Hospital admin system |
| Interaction logs | Call transcripts, chat history, agent decisions | System-generated |
| Knowledge base | Triage protocols, drug interactions | Medical guidelines (WHO, NICE) |

## 5\. Ethics, Privacy, Compliance Informed consent** for AI interaction (verbal at call start, click-through on chat). **Human-in-the-loop** for any decision above the yellow band. ‘’’          The 5-level **Emergency Severity Index (ESI)**: **Levels 1 & 2 (Red/Orange Bands):** Immediate life threats (e.g., anaphylaxis, severe trauma). System architecture must abort AI interaction, trigger a high-priority WebSocket alert to the charge nurse desk, and provide automatic phone routing. **Level 3 (Yellow Band):** Requires multiple resources but stable vitals. This is where your AI context-gathering shines, summarizing the information for the clinician before they step in. **Levels 4 & 5 (Green Blue Bands):** Non-urgent schedules/refills. Fully automatable by your assistant. ‘’’ **Explainability**: show the patient *why* they were routed (e.g., "based on your chest pain and history"). **Compliance posture**: align with **HIPAA** (US), **GDPR** (EU), and local health-data laws. **Bias checks**: validate the risk score across age, sex, and language subgroups.

**NB**

## **Guardrail Placement**

### **1\. The Output Guardrail**

* **Where:** Post-Generation / Pre-Delivery. Positioned directly between the **Triage Agent** and the **User Output Channel**.  
* **Function:** Holds the generated response in a temporary state buffer. It acts as a synchronous interceptor to ensure the AI never delivers a definitive medical diagnosis (e.g., *"You are having a heart attack"*) and strictly sticks to safe triage protocol language.

### **2\. Input Guardrail**

* **Where:** Post-Transcription / Pre-Routing. At the absolute front door before the payload hits the **Router Agent**.  
* **Function:** Sanitizes incoming text/audio data to block jailbreak attempts, adversarial prompt injections, or immediate red-band emergencies that must bypass conversational AI entirely.

flowchart TB
    subgraph LANE_PAT["PATIENT"]
        P1[Calls, chats, or opens app]
        P2[Receives confirmation<br/>and follow-up reminder]
        P3[Outcome: satisfied,<br/>issue resolved]
    end

    subgraph LANE_COMM["COMMUNICATION AGENT  (speaks with the patient)"]
        C1[Answers in under 2 sec]
        C2[Quick registration if new patient]
        C3[Understands need in plain language]
        C4[Sends confirmation and reminder]
    end

    subgraph LANE_HIST["HISTORY AGENT  (remembers the patient)"]
        H1[Greeted by name, history loaded]
    end

    subgraph LANE_TRIAGE["TRIAGE AGENT  (assesses the risk)"]
        T1[Asks focused symptom questions]
        T2[Computes risk score and band]
        T3[Low risk: self-care advice]
    end

    subgraph LANE_SCHED["SCHEDULING AGENT  (books the right resource)"]
        S1[Books routine appointment]
        S2[Books same-day urgent slot]
    end

    subgraph LANE_ESC["ESCALATION AGENT  (reaches a human fast)"]
        E1[Pages on-call clinician]
        E2[Clinician joins with full context]
    end

    P1 --> C1 --> C2 --> C3
    C2 -.if returning.-> H1 --> C3
    C3 --> T1 --> T2 --> T4{Risk}
    T4 -- Low --> T3 --> S1
    T4 -- Medium --> S2
    T4 -- High --> E1 --> E2
    C3 --> S1
    T3 --> C4
    S1 --> C4
    S2 --> C4
    E2 --> C4
    C4 --> P2 --> P3

    classDef lanePat fill:#fafafa,stroke:#616161,color:#212121
    classDef laneComm fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef laneHist fill:#f3e5f5,stroke:#6a1b9a,color:#4a148c
    classDef laneTri fill:#fff3e0,stroke:#e65100,color:#bf360c
    classDef laneSch fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef laneEsc fill:#ffebee,stroke:#c62828,color:#b71c1c
    classDef dec fill:#fffde7,stroke:#f9a825,color:#f57f17

    class P1,P2,P3 lanePat
    class C1,C2,C3,C4 laneComm
    class H1 laneHist
    class T1,T2,T3 laneTri
    class S1,S2 laneSch
    class E1,E2 laneEsc
    class T4 dec


flowchart TB
    %% ============== External Actors ==============
    subgraph PAT[" "]
        direction LR
        P1[Patient<br/>Voice]
        P2[Patient<br/>Chat / Web]
    end

    subgraph CLIN[" "]
        D1[On-call<br/>Clinician]
        D2[GP / Specialist]
    end

    %% ============== Intake ==============
    GW[Intake Gateway<br/>ASR + Channel Router]

    %% ============== Orchestrator ==============
    subgraph ORCH["Orchestration Layer"]
        ORC[Orchestrator<br/>Planner + ReAct Loop]
        ST[(Session State<br/>Memory)]
        POL[Policy Guardrails<br/>Refusals + Red Flags]
    end

    %% ============== Agents ==============
    subgraph AGENTS["Specialist Agents"]
        A1["Triage Agent<br/>Risk Score 0-1"]
        A2["History Agent<br/>Patient Memory"]
        A3["Scheduling Agent<br/>Slots + Resources"]
        A4["Communication Agent<br/>Voice + SMS + Email"]
        A5["Escalation Agent<br/>Clinician Paging"]
    end

    %% ============== RAG Layer ==============
    subgraph RAG["RAG Layer (Retrieval-Augmented Generation)"]
        EMB[Embedder<br/>bge / OpenAI / Cohere]
        VKB[(Vector Store: KB<br/>protocols, guidelines, red-flags)]
        VPH[(Vector Store: Patient<br/>episodic memory, prior visits)]
        VFAQ[(Vector Store: FAQ<br/>hospital policies)]
        RER[Reranker<br/>cross-encoder]
    end

    %% ============== Structured Data ==============
    subgraph DATA["Structured Data"]
        PDB[(Patient DB<br/>Profiles, history)]
        CAL[(Resource Calendar<br/>Doctors, rooms, ER)]
        LOG[(Audit & Metrics Log)]
    end

    %% ============== External Services ==============
    subgraph EXT["External Services"]
        TEL[Telephony<br/>Twilio / Vonage]
        SMS[SMS / Email Gateway]
        PAG[Pager / Alert System]
    end

    %% ============== Flows ==============
    P1 --> GW
    P2 --> GW
    GW --> ORC
    ORC <--> ST
    ORC --> POL

    ORC --> A1
    ORC --> A2
    ORC --> A3
    ORC --> A4
    ORC --> A5

    %% RAG wiring
    A1 --> EMB --> VKB --> RER --> A1
    A2 --> EMB --> VPH --> RER --> A2
    A4 --> EMB --> VFAQ --> RER --> A4
    A2 <--> PDB
    A3 <--> CAL
    A4 --> TEL
    A4 --> SMS
    A5 --> PAG

    A5 --> D1
    A3 --> D2
    A4 --> P1
    A4 --> P2

    ORC --> LOG
    A1 --> LOG
    A2 --> LOG
    A3 --> LOG
    A4 --> LOG
    A5 --> LOG
    EMB --> LOG
    RER --> LOG

    %% ============== Styles ==============
    classDef actor fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef agent fill:#fff3e0,stroke:#e65100,color:#bf360c
    classDef orch fill:#f3e5f5,stroke:#6a1b9a,color:#4a148c
    classDef store fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef ext fill:#fce4ec,stroke:#ad1457,color:#880e4f
    classDef rag fill:#fff9c4,stroke:#f57f17,color:#e65100

    class P1,P2,D1,D2 actor
    class A1,A2,A3,A4,A5 agent
    class ORC,ST,POL,GW orch
    class PDB,CAL,LOG store
    class TEL,SMS,PAG ext
    class EMB,VKB,VPH,VFAQ,RER rag
