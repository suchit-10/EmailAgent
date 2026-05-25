# Architecture

## System Diagram

```mermaid
flowchart TB
  user[User]

  subgraph client[Frontend - Next.js 15]
    ui[Email workspace UI]
    console[Agent console]
    dashboard[Recruiter dashboard]
    apiClient[API client]
  end

  subgraph api[Backend - FastAPI]
    authApi[Auth routes]
    agentApi[Agent routes]
    emailApi[Email routes]
    dashboardApi[Dashboard routes]
    deps[Session and DB dependencies]
  end

  subgraph agent[LangGraph Email Agent]
    memory[Store conversation memory]
    planner[Create execution plan]
    router[Route by intent]
    search[Search synced email]
    summarize[Summarize results]
    classify[Classify email]
    draft[Prepare email draft]
    calendar[Prepare calendar action]
    final[Final response]
  end

  subgraph llm[LLM Layer]
    modelRouter[Model router]
    groq[Groq OpenAI-compatible API]
  end

  subgraph tools[Tool Layer]
    gmailReader[Gmail reader]
    gmailSearch[Gmail keyword search]
    gmailSender[Gmail sender and drafts]
    calendarTool[Google Calendar tool]
    vectorSearch[Vector search tool]
    ocr[Attachment and OCR tools]
  end

  subgraph data[Data Stores]
    postgres[(PostgreSQL)]
    chroma[(ChromaDB)]
  end

  subgraph workers[Background Workers]
    sync[Email sync worker]
    digest[Daily digest worker]
    followup[Follow-up worker]
  end

  subgraph google[Google APIs]
    oauth[Google OAuth]
    gmail[Gmail API]
    gcal[Google Calendar API]
  end

  user --> ui
  ui --> apiClient
  console --> apiClient
  dashboard --> apiClient
  apiClient --> authApi
  apiClient --> agentApi
  apiClient --> emailApi
  apiClient --> dashboardApi

  authApi --> oauth
  oauth --> authApi
  authApi --> postgres
  deps --> postgres

  agentApi --> deps
  emailApi --> deps
  dashboardApi --> deps
  agentApi --> agent

  memory --> planner
  planner --> router
  router --> search
  router --> draft
  router --> final
  search --> summarize
  search --> classify
  classify --> calendar
  summarize --> final
  draft --> final
  calendar --> final

  planner --> modelRouter
  summarize --> modelRouter
  classify --> modelRouter
  draft --> modelRouter
  final --> modelRouter
  modelRouter --> groq

  search --> gmailSearch
  search --> vectorSearch
  draft --> gmailSender
  calendar --> calendarTool
  ocr --> agent

  gmailSearch --> postgres
  vectorSearch --> chroma
  gmailSender --> gmail
  calendarTool --> gcal

  emailApi --> sync
  emailApi --> digest
  emailApi --> followup
  sync --> gmailReader
  gmailReader --> gmail
  sync --> postgres
  sync --> chroma
  sync --> dashboardApi
  digest --> postgres
  digest --> modelRouter
  followup --> postgres
  followup --> modelRouter

  dashboardApi --> postgres
```

## Request Flow

```mermaid
sequenceDiagram
  actor User
  participant UI as Next.js UI
  participant API as FastAPI
  participant Agent as LangGraph Agent
  participant LLM as Model Router and Groq
  participant DB as PostgreSQL
  participant Vector as ChromaDB
  participant Google as Gmail or Calendar API

  User->>UI: Ask email question or request draft
  UI->>API: POST /api/agent/invoke or /stream
  API->>DB: Resolve current user and session
  API->>Agent: Invoke graph with user message
  Agent->>DB: Store user memory
  Agent->>LLM: Create structured plan
  LLM-->>Agent: Intent and tool plan
  Agent->>DB: Keyword search synced emails
  Agent->>Vector: Semantic search synced emails
  Agent->>LLM: Summarize, classify, or draft response
  opt Needs Google action
    Agent->>Google: Read, draft, send, or prepare calendar action
  end
  Agent->>DB: Store assistant memory or draft metadata
  Agent-->>API: Final response, draft, or event data
  API-->>UI: JSON or server-sent events
  UI-->>User: Render answer and approval UI
```

## Data Sync Flow

```mermaid
flowchart LR
  syncButton[Sync inbox action] --> emailApi[POST /api/emails/sync]
  emailApi --> token[Load encrypted Google token]
  token --> gmail[Gmail API]
  gmail --> worker[EmailSyncWorker]
  worker --> classify[Rule-based classification and urgency]
  classify --> messages[(email_messages)]
  classify --> leads[(recruiter_leads)]
  worker --> embeddings[(ChromaDB email collection)]
  messages --> dashboard[Dashboard and search APIs]
  embeddings --> agentSearch[Agent semantic search]
```

## Runtime Containers

```mermaid
flowchart LR
  browser[Browser] --> frontend[frontend:3000]
  frontend --> backend[backend:8000]
  backend --> postgres[(postgres:5432)]
  backend --> chromadb[(chromadb:8000)]
  backend --> google[Google APIs]
  backend --> groq[Groq API]
```

## Boundaries

- Frontend owns the interactive workspace, dashboard, chat console, loading states, and approval UX.
- FastAPI owns auth, HTTP sessions, validation, orchestration routes, and service dependencies.
- LangGraph owns typed agent state, workflow routing, retries, and tool execution.
- Tool modules own Gmail, Calendar, attachment parsing, OCR, and vector-search integration.
- PostgreSQL stores users, encrypted Google tokens, synced emails, conversation memory, recruiter leads, and outbound drafts.
- ChromaDB stores email embeddings for semantic retrieval.
- Provider logic is isolated under `backend/services/llm` so Groq can be replaced with another provider adapter.
