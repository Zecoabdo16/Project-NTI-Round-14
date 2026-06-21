**Hospital Patient Agentic System**

# 1. Stack {#stack}

| **Layer**              | **Free Tool**         |
|------------------------|-----------------------|
| Interface              | Streamlit             |
| Vector DB (memory)     | ChromaDB              |
| LLM (classifier + RAG) | Groq + LLaMA-3        |
| Agent framework        | LangGraph             |
| Web search             | DuckDuckGo API        |
| Resource DB            | SQLite                |
| Case log (handoff)     | SQLite or JSON file   |
| Embeddings             | sentence-transformers |

# 2. Agent Architecture {#agent-architecture}

## 2.1 Layer overview {#layer-overview}

The system is organized into six layers, each with a clear responsibility:

- Interface layer: Streamlit chat UI receives patient input

- Memory layer: ChromaDB retrieves relevant user history and feeds it to the classifier and orchestrator

- Classification layer: Classifier agent outputs both an intent label and a priority score

- Orchestration layer: LangGraph orchestrator routes to the right tool based on intent; escalates on high score

- Tool layer: Four tools handle web search, bookings, medical queries, and general hospital info

- Resource layer: SQLite DB tracks available slots; availability agent handles get, update, and notify operations

## 2.2 Agent responsibilities {#agent-responsibilities}

| **Agent** | **Input** | **Output** |
|----|----|----|
| Classifier | Patient message + user history | Intent label + priority/loyalty score (0--1 float) |
| Orchestrator | Intent label + priority score + memory context | Dispatches to correct tool; halts on high-priority escalation |
| Reservation agent | Booking intent + patient ID | Calls get(), update(), notify() on SQLite resource DB |
| Medical RAG | Medical query text | Retrieved answer from FAISS clinical knowledge base |
| Services RAG | General info query | Retrieved answer from ChromaDB hospital services index |
| Availability agent | Resource DB | Checks slots, updates bookings, notifies patient |

## 2.3 Intent routing logic {#intent-routing-logic}

The classifier outputs one of four intent labels. The orchestrator uses this label to route the request:

| **Intent label** | **Routes to** | **Example trigger** |
|----|----|----|
| booking | Reservation agent | \'I want to book an appointment for next Monday\' |
| medical | Medical RAG | \'What are the side effects of ibuprofen?\' |
| general_info | Services RAG + web search | \'What are your visiting hours?\' |
| escalate | Human handoff (terminal) | High priority score OR sensitive/emergency keywords |

## 2.4 Human handoff (terminal state) {#human-handoff-terminal-state}

When the priority/loyalty score exceeds the escalation threshold, or when emergency keywords are detected, the system enters a terminal handoff state:

- The agent immediately stops processing

- A case log entry is written to SQLite with the full conversation context, intent label, and score

# 3. RAG Pipeline Details {#rag-pipeline-details}

## 3.1 Medical RAG {#medical-rag}

- Embedding model: sentence-transformers/all-MiniLM-L6-v2

- Vector store: ChromaDB

- Retrieval: top-k = 3 chunks, similarity threshold = 0.75

- LLM answer generation: Groq + LLaMA-3 with retrieved context in prompt

- Evaluation metrics: Hit Rate, MRR, Faithfulness, Answer Relevance (DeepEval)

## 3.2 Services RAG {#services-rag}

- Embedding model: sentence-transformers/all-MiniLM-L6-v2

- Vector store: ChromaDB collection for hospital services (visiting hours, departments, pricing)

- Retrieval: top-k = 2 chunks

- LLM answer generation: Groq + LLaMA-3

# 4. Implementation Steps for the Tech Team {#implementation-steps-for-the-tech-team}

## Step 1 --- Environment setup {#step-1-environment-setup}

- Create a Python virtual environment: python -m venv venv

- Install dependencies from requirements.txt

- Key packages: langchain, langgraph, chromadb, faiss-cpu, sentence-transformers, streamlit, groq, duckduckgo-search

## Step 2 --- Build the embeddings and indexes {#step-2-build-the-embeddings-and-indexes}

- Place medical PDF documents in data/medical_docs/

- Place hospital services info in data/services_docs/

- Run the indexing script to build ChromaDB (for services and for medical info) indexes

- Verify retrieval quality with a few test queries before wiring to the LLM

## Step 3 --- Implement the classifier agent {#step-3-implement-the-classifier-agent}

- Prompt LLaMA-3 via Groq to return a JSON with two fields: intent (string) and score (float 0 to 1)

- Intent values: booking, medical, general_info, escalate

- Score represents urgency/priority --- values above 0.8 trigger human handoff

- Include recent user history from ChromaDB in the classifier prompt for context

## Step 4 --- Build the LangGraph orchestrator {#step-4-build-the-langgraph-orchestrator}

- Define nodes: classifier, router, reservation_agent, medical_rag, services_rag, human_handoff

- Define edges: classifier -\> router; router branches on intent label; high score -\> human_handoff

- Human handoff node writes to case_logs.db and returns END state

- All other nodes return their tool output to a response formatter

## Step 5 --- Implement the reservation agent {#step-5-implement-the-reservation-agent}

- get(): query SQLite resources.db for available slots by date/department

- update(): write confirmed booking back to resources.db

- notify(): log a notification entry (can later be extended to email/SMS)

- Availability agent wraps these three operations and is called by the reservation agent

## Step 6 --- Build the Streamlit {#step-6-build-the-streamlit}

- chat interface that takes patient text input

- Pass input to the LangGraph graph and display the returned response

- Show a clear indicator when a case has been escalated to a human agent

## Step 7 --- Evaluate RAG quality {#step-7-evaluate-rag-quality}

- Use DeepEval to measure Hit Rate, MRR, Faithfulness, and Answer Relevance on a test set

- Adjust top-k and similarity threshold based on evaluation results

- Minimum acceptable Faithfulness score: 0.75
