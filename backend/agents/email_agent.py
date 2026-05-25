from langgraph.graph import END, START, StateGraph
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.agents.state import AgentPlan, AgentState, EmailClassification
from backend.auth.google_oauth import get_google_credentials
from backend.db.models import ConversationMemory, EmailMessage, GoogleToken, OutboundDraft, User
from backend.services.llm.model_router import ModelRouter, ModelTask
from backend.tools.calendar_tool import CalendarTool
from backend.tools.gmail_search import GmailSearchTool
from backend.tools.vector_search import VectorSearchTool


SYSTEM = """You are an AI-native email operating system. Plan tool use carefully, preserve user privacy,
require approval before sending email, and keep responses concise and actionable."""


class EmailAgent:
    def __init__(self, db: AsyncSession, router: ModelRouter | None = None) -> None:
        self.db = db
        self.router = router or ModelRouter()
        self.keyword_search = GmailSearchTool(db)
        self.vector_search = VectorSearchTool()

    async def plan_node(self, state: AgentState) -> AgentState:
        structured = await self.router.provider.structured(
            model=self.router.model_for(ModelTask.PLANNING),
            schema=AgentPlan,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"Create an execution plan for: {state['message']}"},
            ],
        )
        return {"plan": structured}

    async def memory_node(self, state: AgentState) -> AgentState:
        self.db.add(ConversationMemory(user_id=state["user_id"], role="user", content=state["message"], context={}))
        await self.db.commit()
        return {"memories": []}

    async def access_status_node(self, state: AgentState) -> AgentState:
        user = await self.db.get(User, state["user_id"])
        token = await self.db.scalar(select(GoogleToken).where(GoogleToken.user_id == state["user_id"]))
        synced = await self.db.scalar(select(func.count()).select_from(EmailMessage).where(EmailMessage.user_id == state["user_id"]))
        if token is None:
            response = "I do not have Gmail access yet. Click Connect Gmail and complete Google consent first."
        else:
            response = (
                f"Yes. This app is connected to {user.email if user else 'your Google account'} through Google OAuth. "
                f"I have the requested Gmail/Calendar token stored encrypted, and {synced or 0} emails are currently synced locally. "
                "If you want me to summarize mail, use the inbox sync button first when the synced count is 0."
            )
        return {"final_response": response}

    async def search_node(self, state: AgentState) -> AgentState:
        plan = state["plan"]
        query = plan.search_query or state["message"]
        semantic_hits = await self.vector_search.semantic_email_search(str(state["user_id"]), query=query, limit=8)
        keyword_hits = await self.keyword_search.keyword_search(state["user_id"], query=query, limit=8)
        emails = [
            {
                "id": email.gmail_message_id,
                "sender": email.sender,
                "subject": email.subject,
                "snippet": email.snippet,
                "body": email.body_text[:4000],
                "received_at": email.received_at.isoformat() if email.received_at else None,
                "classification": email.classification,
            }
            for email in keyword_hits
        ]
        emails.extend({"id": hit["metadata"].get("message_id"), "snippet": hit["document"], "semantic_score": hit["distance"]} for hit in semantic_hits)
        return {"emails": emails[:12]}

    async def summarize_node(self, state: AgentState) -> AgentState:
        emails = state.get("emails", [])
        if not emails:
            return {
                "final_response": (
                    "I do not see any synced emails yet. Use the inbox sync button on the left, "
                    "then ask me again to summarize unread or recruiter emails."
                )
            }
        content = "\n\n".join(f"From: {e.get('sender')}\nSubject: {e.get('subject')}\n{e.get('snippet')}" for e in emails)
        summary = await self.router.provider.complete(
            model=self.router.model_for(ModelTask.SUMMARY),
            messages=[
                {"role": "system", "content": "Summarize email search results into crisp bullets with next actions."},
                {"role": "user", "content": content or state["message"]},
            ],
        )
        return {"final_response": summary}

    async def classify_node(self, state: AgentState) -> AgentState:
        classifications = []
        for email in state.get("emails", [])[:6]:
            parsed = await self.router.provider.structured(
                model=self.router.model_for(ModelTask.CLASSIFICATION),
                schema=EmailClassification,
                messages=[
                    {"role": "system", "content": "Classify the email and extract urgency, company, role, and deadlines."},
                    {"role": "user", "content": str(email)},
                ],
            )
            classifications.append(parsed.model_dump())
        return {"classifications": classifications}

    async def send_email_node(self, state: AgentState) -> AgentState:
        draft_text = await self.router.provider.complete(
            model=self.router.model_for(ModelTask.FINAL_RESPONSE),
            messages=[
                {"role": "system", "content": "Draft a professional email. Return subject and body."},
                {"role": "user", "content": state["message"]},
            ],
        )
        draft = OutboundDraft(user_id=state["user_id"], to=[], subject="AI generated draft", body=draft_text)
        self.db.add(draft)
        await self.db.commit()
        return {"draft": {"id": str(draft.id), "subject": draft.subject, "body": draft.body, "status": draft.status}}

    async def calendar_node(self, state: AgentState) -> AgentState:
        await get_google_credentials(self.db, state["user_id"])
        return {"calendar_events": [], "final_response": "I found calendar-related intent. Extracted interview times need confirmation before events are created."}

    async def attachment_processing_node(self, state: AgentState) -> AgentState:
        return {"attachments": []}

    async def final_node(self, state: AgentState) -> AgentState:
        if state.get("final_response"):
            response = state["final_response"]
        elif state.get("draft"):
            response = "I prepared a draft and marked it pending approval before sending."
        else:
            response = await self.router.provider.complete(
                model=self.router.model_for(ModelTask.FINAL_RESPONSE),
                messages=[
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": f"Answer based on state: {state}"},
                ],
            )
        self.db.add(ConversationMemory(user_id=state["user_id"], role="assistant", content=response, context={}))
        await self.db.commit()
        return {"final_response": response}

    def route_after_plan(self, state: AgentState) -> str:
        intent = state["plan"].intent
        message = state["message"].lower()
        if any(phrase in message for phrase in ["access to my mail", "access to my gmail", "linked with my gmail", "gmail connected"]):
            return "access_status"
        if intent in {"search", "dashboard"}:
            return "search"
        if intent in {"summarize", "digest"}:
            return "search"
        if intent in {"draft_reply", "send_email"}:
            return "send_email"
        if intent == "calendar":
            return "search"
        return "final"

    def route_after_search(self, state: AgentState) -> str:
        intent = state["plan"].intent
        if intent == "calendar":
            return "classify"
        return "summarize"

    def compile(self):
        graph = StateGraph(AgentState)
        graph.add_node("store_memory", self.memory_node)
        graph.add_node("create_plan", self.plan_node)
        graph.add_node("check_access_status", self.access_status_node)
        graph.add_node("search_emails", self.search_node)
        graph.add_node("summarize_emails", self.summarize_node)
        graph.add_node("classify_emails", self.classify_node)
        graph.add_node("draft_email", self.send_email_node)
        graph.add_node("prepare_calendar", self.calendar_node)
        graph.add_node("process_attachments", self.attachment_processing_node)
        graph.add_node("finish_response", self.final_node)
        graph.add_edge(START, "store_memory")
        graph.add_edge("store_memory", "create_plan")
        graph.add_conditional_edges(
            "create_plan",
            self.route_after_plan,
            {
                "access_status": "check_access_status",
                "search": "search_emails",
                "send_email": "draft_email",
                "final": "finish_response",
            },
        )
        graph.add_conditional_edges(
            "search_emails",
            self.route_after_search,
            {
                "classify": "classify_emails",
                "summarize": "summarize_emails",
            },
        )
        graph.add_edge("classify_emails", "prepare_calendar")
        graph.add_edge("prepare_calendar", "finish_response")
        graph.add_edge("check_access_status", "finish_response")
        graph.add_edge("summarize_emails", "finish_response")
        graph.add_edge("draft_email", "finish_response")
        graph.add_edge("process_attachments", "finish_response")
        graph.add_edge("finish_response", END)
        return graph.compile()
