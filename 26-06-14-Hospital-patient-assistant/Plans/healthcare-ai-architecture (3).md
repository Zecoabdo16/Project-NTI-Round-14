# نظام الـ AI Agents للرعاية الصحية - مخططات الهيكلية

## 1) الهيكل العام الكامل للنظام

يوضح هذا المخطط جميع الـ Agents الأساسية والأنظمة/الأدوات المتصلة بكل واحد منها، بدءًا من قنوات التواصل مع المريض وحتى قواعد البيانات الخلفية.

```mermaid
graph TD
    P1[Patient]
    P2[Phone / IVR]
    P3[WhatsApp]
    P4[Mobile app]
    P1 --> P2
    P1 --> P3
    P1 --> P4
    P2 --> ORCH
    P3 --> ORCH
    P4 --> ORCH

    ORCH["Orchestrator agent - Claude/GPT<br/>Intent classification, routing, context"]

    %% Agent 1: Triage and priority
    ORCH --> TRIAGE[Triage and Priority Agent]
    TRIAGE --> SEVERITY[Symptom severity classifier]
    SEVERITY --> CRITICAL{Critical case?}
    CRITICAL -->|Yes| ERFAST[Fast-track to ER and alert staff]
    CRITICAL -->|No| ORCH

    %% Agent 2: Availability
    ORCH --> AVAIL[Availability Agent]
    AVAIL --> DOCSCHED[(Doctor schedules - HIS)]
    AVAIL --> BEDS[(Bed management system)]
    AVAIL --> EQUIP[(Equipment status API)]

    %% Agent 3: Queue and callback
    ORCH --> QUEUE[Queue and Callback Agent]
    QUEUE --> QLEN[Queue length and wait estimate]
    QLEN --> CALLBACK[Callback scheduler]
    CALLBACK --> SMS[(SMS / WhatsApp gateway)]

    %% Agent 4: History and CRM
    ORCH --> HIST[Patient History and CRM Agent]
    HIST --> EHRLOOKUP[EHR lookup]
    HIST --> LOYALTY[CRM loyalty and visit history]
    LOYALTY --> CRMDB[(CRM database)]
    EHRLOOKUP --> GENCHECK{Genetic report exists?}
    GENCHECK -->|Yes| GENMERGE[Merge genetic summary]
    GENCHECK -->|No| GENSKIP[Continue with standard history]
    GENMERGE --> EHRDB[(EHR database)]
    GENSKIP --> EHRDB

    %% Agent 5: Consultation analysis
    ORCH --> CONSULT[Consultation Analysis Agent]
    CONSULT --> RECORD[Audio recording - with consent]
    RECORD --> STT[Speech-to-text and diarization]
    STT --> NLP[NLP extraction]
    NLP --> QBANK[Specialty question bank]
    NLP --> PATINFO[Patient info extracted]
    PATINFO --> EHRLOOKUP
    QBANK --> QBANKDB[(Question bank database)]

    classDef patient fill:#F1EFE8,stroke:#5F5E5A,color:#2C2C2A
    classDef agent fill:#EEEDFE,stroke:#534AB7,color:#26215C
    classDef step fill:#E1F5EE,stroke:#0F6E56,color:#04342C
    classDef decision fill:#FAEEDA,stroke:#854F0B,color:#412402
    classDef data fill:#F1EFE8,stroke:#888780,color:#2C2C2A
    classDef alert fill:#FAECE7,stroke:#993C1D,color:#4A1B0C

    class P1,P2,P3,P4 patient
    class ORCH,TRIAGE,AVAIL,QUEUE,HIST,CONSULT agent
    class SEVERITY,QLEN,CALLBACK,EHRLOOKUP,LOYALTY,GENMERGE,GENSKIP,RECORD,STT,NLP,QBANK,PATINFO step
    class CRITICAL,GENCHECK decision
    class DOCSCHED,BEDS,EQUIP,SMS,EHRDB,CRMDB,QBANKDB data
    class ERFAST alert
```

---

## 2) مسار تحليل الكشف بالتفصيل

يوضح هذا المخطط التفاصيل الكاملة لمسار "Consultation Analysis Agent": من بداية الكشف، عبر التسجيل الصوتي والتفريغ النصي وفصل المتحدثين، وحتى تحديث الـ History وبنك الأسئلة، مع التعامل مع وجود أو عدم وجود تقرير جيني للمريض.

```mermaid
graph TD
    START[Consultation starts - doctor and patient]
    START --> CONSENT{Recording consent given?}
    CONSENT -->|No| MANUAL[Doctor enters notes manually]
    CONSENT -->|Yes| RECORD[Record audio]
    RECORD --> STT[Speech-to-text]
    STT --> DIARIZE[Speaker diarization]
    DIARIZE --> DOCTORLINES[Doctor's questions and statements]
    DIARIZE --> PATIENTLINES[Patient's answers and statements]

    DOCTORLINES --> QEXTRACT[Extract question patterns]
    QEXTRACT --> QCOMPARE{Already in question bank?}
    QCOMPARE -->|No| QADD[Add new question to specialty bank]
    QCOMPARE -->|Yes| QSKIP[Skip - already covered]
    QADD --> QBANKDB[(Specialty question bank DB)]
    QSKIP --> QBANKDB

    PATIENTLINES --> INFOEXTRACT["Extract patient info<br/>symptoms, meds, allergies, family history"]
    INFOEXTRACT --> GENCHECK{Genetic report exists for patient?}
    GENCHECK -->|Yes| GENFETCH[Fetch genetic summary from lab DB]
    GENCHECK -->|No| GENNONE[No genetic data attached]
    GENFETCH --> MERGE[Merge into patient record]
    GENNONE --> MERGE
    INFOEXTRACT --> MERGE
    MANUAL --> EHRUPDATE[(Update patient EHR / history)]
    MERGE --> EHRUPDATE

    classDef start fill:#F1EFE8,stroke:#5F5E5A,color:#2C2C2A
    classDef step fill:#EEEDFE,stroke:#534AB7,color:#26215C
    classDef decision fill:#FAEEDA,stroke:#854F0B,color:#412402
    classDef output fill:#E1F5EE,stroke:#0F6E56,color:#04342C
    classDef alt fill:#FAECE7,stroke:#993C1D,color:#4A1B0C
    classDef data fill:#F1EFE8,stroke:#888780,color:#2C2C2A

    class START,MANUAL start
    class CONSENT,QCOMPARE,GENCHECK decision
    class RECORD,STT,DIARIZE,QEXTRACT,INFOEXTRACT,MERGE,GENFETCH step
    class DOCTORLINES,PATIENTLINES,QADD,GENNONE output
    class QSKIP alt
    class QBANKDB,EHRUPDATE data
```

---

## ملاحظات الاستخدام

```js
// مثال استخدام
import mermaid from "mermaid";
const { svg } = await mermaid.render("full-arch", fullArchitectureDiagram);
const { svg: svg2 } = await mermaid.render("consult-flow", consultationDetailedFlow);
```
