# CarePlus Medical Assistant Agent

A full-stack medical assistant agent that manages user health data and provides helpful insights. Built with FastAPI, React, Agno, OpenAI GPT-4o-mini, and PostgreSQL.

## Features

- Greeting and onboarding
- Phlebotomist test scheduling with confirmation
- Address change management
- Blood result storage and trend analysis
- Physician consultation requests
- Medication tracking, reminders, and adherence
- Prescription refill management
- Health history timeline with trend detection
- Health profile summary (allergies, conditions, procedures, family history)
- Appointment modification and cancellation
- Upcoming appointment listing
- Symptom assessment with triage guidance
- Emergency detection and escalation

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.12) |
| Frontend | React + Vite + TypeScript + TailwindCSS |
| Agent Framework | Agno |
| LLM | OpenAI GPT-4o-mini |
| Database | PostgreSQL 16 |
| Orchestration | Docker Compose |

## Quick Start

1. Clone the repository and copy the environment file:

```bash
cp .env.example .env
```

2. Add your OpenAI API key to `.env`:

```
OPENAI_API_KEY=sk-your-key-here
```

3. Start all services with Docker Compose:

```bash
docker compose up --build
```

4. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Project Structure

```
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       ├── models/
│       ├── schemas/
│       ├── agent/
│       ├── tools/
│       ├── routes/
│       └── seed.py
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
└── db/
    └── init.sql
```

## Development

### Backend only

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend only

```bash
cd frontend
npm install
npm run dev
```

## Demo User

The application seeds a demo user (ID: 1) with pre-populated health data including medications, blood results, appointments, and health profile information.
