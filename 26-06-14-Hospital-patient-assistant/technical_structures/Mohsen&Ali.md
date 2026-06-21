# Technical Approach – Agentic Medical System

Framework: LangGraph + FastAPI

## 1- Orchestrator Agent

Function:
Acts as the central coordinator and the only agent that communicates directly with patients.
Responsible for authentication, session management, query understanding, and routing requests to the appropriate agent.

Input:
- Patient Profile
- Medical History
- Patient Query (Text / Voice / Image)

Output:
- Routes request to Scheduling Agent, Diagnosis Agent, Emergency Agent, or Feedback Agent
- Returns final response to patient

Tools:
- Patient Database
- Session Management Service

Model:
- Gemini Flash 2.5

---

## 2- Scheduling Agent

Function:
Handles appointment booking and clinic availability checks.
Manages loyalty points and applies eligible offers during payment.

Input:
- Orchestrator Output
- Appointment Request
- Department Recommendation

Output:
- Available Appointment Slots
- Booking Confirmation
- Loyalty Information

Tools:
- Doctor Database (Read)
- Appointment Database (Read / Write)
- add_points()
- check_available_offers()

Model:
- Llama 3.2

---

## 3- Diagnosis Agent

Function:
Analyzes patient symptoms and medical data to determine the most appropriate department and urgency level.

Input:
- Patient Complaint (Text / Voice / Image)
- Medical History

Output:
- Department Classification
- Confidence Score
- Urgency Score
- Recommendation to Scheduling Agent or Emergency Agent

Tools:
- Medical RAG System
- Vector Database (Qdrant)
- Medical Knowledge Base

Model:
- Qwen2.5-VL (for image understanding)

---

## 4- Emergency Agent

Function:
Handles urgent and life-threatening situations.
Determines ambulance requirements and generates emergency alerts.

Input:
- Diagnosis Agent Output
- Patient Risk Profile

Output:
- Emergency Alert
- Ambulance Recommendation
- Hospital Notification

Tools:
- Emergency Rules Engine
- Patient History Database

Model:
- Llama 3.2

---

## 5- Feedback Agent

Function:
Collects patient feedback after appointments and stores insights for analytics and future model improvements.

Input:
- Completed Appointment Information

Output:
- Satisfaction Score
- Complaint Records
- Patient Health Status Updates

Tools:
- Analytics Database
- Feedback Database

Model:
- Qwen 0.5

---

## Supporting Services

### Medical RAG Service

Function:
Provides medical knowledge retrieval for the Diagnosis Agent.

Components:
- Document Ingestion Pipeline
- Embedding Model
- Qdrant Vector Database
- Retrieval Layer

Output:
- Relevant Medical Context

---

### Notification Service

Function:
Sends notifications to patients.

Used For:
- Appointment Reminders
- Medication Reminders
- Feedback Requests
- Emergency Alerts

Channel:
- Telegram Bot API

---

### Medication Reminder Service

Function:
Automatically schedules medication reminders after prescriptions are stored.

Input:
- Prescription Data

Output:
- Reminder Notifications

Tools:
- PostgreSQL
- Cron Jobs
- Telegram Bot API

---

## Databases

### Patient Database

Stores:
- Patient Profiles
- Medical History
- Loyalty Points
- Previous Diagnoses

### Appointment Database

Stores:
- Doctors
- Clinics
- Appointments
- Availability Slots

### Analytics Database

Stores:
- Feedback Records
- KPIs
- Service Analytics

---

## Monitoring

Tool:
- Langfuse

Purpose:
- Agent Tracing
- Workflow Monitoring
- Performance Evaluation

---

## Technology Stack

Frontend:
- Vue.js
- Tailwind CSS

Backend:
- FastAPI
- Python

Agent Framework:
- LangGraph

Models:
- Qwen 3
- Qwen2.5-VL

Speech-to-Text:
- Whisper Large V3

Text-to-Speech:
- Kokoro TTS

Vector Database:
- Qdrant

Relational Database:
- PostgreSQL

Monitoring:
- Langfuse

Notifications:
- Telegram Bot API
