# AI Email Agent Platform
<img width="1345" height="678" alt="image" src="https://github.com/user-attachments/assets/1989978e-ae65-4d9d-89f8-850fb1faa1e2" />
<img width="711" height="107" alt="image" src="https://github.com/user-attachments/assets/b8644112-3b26-48a7-b481-fa0fb2417157" />


Production-grade scaffold for an AI-native Gmail operating system: FastAPI, LangGraph, Groq model routing, Gmail/Calendar tools, PostgreSQL memory, Chroma semantic search, and a Next.js 15 workspace UI.

## What is included

- Google OAuth2 with encrypted token storage
- Provider-agnostic LLM layer using Groq's OpenAI-compatible endpoint
- Intelligent model routing for summaries, planning, and final responses
- Typed LangGraph workflow with search, summarize, classify, memory, send-email, calendar, and attachment nodes
- Modular Gmail, Calendar, vector search, OCR, and PDF tools
- PostgreSQL schema for users, tokens, emails, memory, recruiter leads, and outbound drafts
- Next.js SaaS UI with chat, inbox intelligence, recruiter dashboard, dark mode, and loading states
- Live inbox sync, search, recruiter lead extraction, daily digest, follow-up drafting, and Gmail draft approval endpoints
- Docker Compose for Postgres, ChromaDB, FastAPI, and Next.js
- Mermaid architecture, workflow, and ER diagrams in `docs/`

## Setup

1. Copy env files:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

2. Generate a Fernet key for `TOKEN_ENCRYPTION_KEY`:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

3. Fill in:

- `GROQ_API_KEY`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `JWT_SECRET`

4. Start services:

```bash
docker compose up --build
```

5. Open:

- Frontend: `http://localhost:3000`
- Backend health: `http://localhost:8000/health`
- ChromaDB: `http://localhost:8001`

## Local development without Docker

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Security notes

- Gmail tokens are encrypted with Fernet before storage.
- The backend sets an HTTP-only session cookie after Google OAuth.
- Sending email is designed around a draft/approval workflow.
- Secrets live in environment variables only.
- Rate limiting hooks are installed through `slowapi`; tune endpoint limits before public deployment.

## Next production steps

- Add Alembic migrations from `backend/db/models.py`.
- Schedule the Gmail sync, daily digest, and follow-up workers with a durable job runner.
- Add human-in-the-loop approval screens for Calendar creation.
- Add LangSmith/OpenTelemetry tracing for agent observability.
