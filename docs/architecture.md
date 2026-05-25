# Architecture

```mermaid
flowchart LR
  User[User] --> UI[Next.js 15 AI Email Workspace]
  UI --> API[FastAPI API]
  API --> Auth[Google OAuth2]
  API --> Agent[LangGraph Email Agent]
  Agent --> Router[Model Router]
  Router --> Groq[Groq OpenAI-Compatible API]
  Agent --> GmailTools[Gmail Tools]
  Agent --> Calendar[Calendar Tool]
  Agent --> Memory[Conversation Memory]
  Agent --> Vector[ChromaDB Vector Search]
  GmailTools --> Gmail[Gmail API]
  Calendar --> GCal[Google Calendar API]
  API --> Postgres[(PostgreSQL)]
  Memory --> Postgres
  Vector --> Chroma[(ChromaDB)]
```

## Boundaries

- Frontend owns the interactive workspace, loading states, and approval UX.
- FastAPI owns auth, sessions, streaming, validation, rate limiting, and orchestration endpoints.
- LangGraph owns typed agent state, workflow routing, retries, and tool execution.
- Provider logic is isolated under `backend/services/llm` so Groq can be replaced with OpenAI, Anthropic, or Gemini adapters.
