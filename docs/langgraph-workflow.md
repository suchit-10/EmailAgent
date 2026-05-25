# LangGraph Workflow

```mermaid
flowchart TD
  Start([START]) --> Memory[memory node]
  Memory --> Plan[planning/reasoning node]
  Plan -->|search, summarize, digest, dashboard| Search[search node]
  Plan -->|draft_reply, send_email| Send[send-email node]
  Plan -->|general| Final[final response node]
  Search -->|calendar intent| Classify[classify node]
  Search -->|search or digest| Summarize[summarize node]
  Classify --> Calendar[calendar node]
  Calendar --> Final
  Summarize --> Final
  Send --> Final
  Final --> End([END])
```

The graph uses typed state in `backend/agents/state.py`, structured outputs for planning and classification, and explicit model routing:

- Summaries: `mixtral-8x7b-32768`
- Planning/reasoning: `deepseek-r1-distill-llama-70b`
- Final user responses: `llama-3.3-70b-versatile`
