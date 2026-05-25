# Architecture

## System View

```mermaid
flowchart LR
  user[User] --> web[Next.js frontend]
  web --> api[FastAPI backend]

  api --> auth[Google OAuth]
  api --> agent[LangGraph email agent]
  api --> workers[Email workers]
  api --> db[(PostgreSQL)]

  agent --> llm[Model router]
  llm --> groq[Groq API]

  agent --> tools[Gmail, Calendar and search tools]
  workers --> tools

  tools --> google[Google APIs]
  tools --> vector[(ChromaDB)]
  tools --> db
```

## Agent Flow

```mermaid
flowchart LR
  request[User request] --> memory[Store memory]
  memory --> plan[Plan intent]
  plan --> route{Intent}
  route -->|search or summarize| search[Search email]
  route -->|draft reply| draft[Create draft]
  route -->|calendar| classify[Classify email]
  route -->|general| answer[Answer]
  search --> summarize[Summarize results]
  classify --> calendar[Prepare calendar action]
  summarize --> answer
  draft --> answer
  calendar --> answer
```

## Main Components

- `frontend/` contains the Next.js workspace, agent console, inbox UI, and recruiter dashboard.
- `backend/api/` exposes auth, agent, email, and dashboard routes through FastAPI.
- `backend/agents/` contains the LangGraph workflow that plans, searches, drafts, summarizes, and responds.
- `backend/tools/` wraps Gmail, Calendar, attachment parsing, OCR, and vector search operations.
- `backend/workers/` syncs Gmail data, builds daily digests, and drafts follow-ups.
- `backend/services/llm/` routes LLM tasks to Groq through an OpenAI-compatible provider layer.
- PostgreSQL stores users, encrypted tokens, synced emails, conversation memory, recruiter leads, and drafts.
- ChromaDB stores email embeddings for semantic search.

## Runtime

```mermaid
flowchart LR
  browser[Browser] --> frontend[frontend:3000]
  frontend --> backend[backend:8000]
  backend --> postgres[(postgres:5432)]
  backend --> chroma[(chromadb:8000)]
  backend --> google[Google APIs]
  backend --> groq[Groq API]
```
