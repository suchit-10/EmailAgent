import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from backend.agents.email_agent import EmailAgent
from backend.api.deps import current_user_id, db_session
from backend.schemas.email import AgentRequest


router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/invoke")
async def invoke_agent(
    request: AgentRequest,
    user_id: str = Depends(current_user_id),
    db: AsyncSession = Depends(db_session),
) -> dict:
    graph = EmailAgent(db).compile()
    result = await graph.ainvoke({"user_id": user_id, "message": request.message, "conversation_id": request.conversation_id, "errors": []})
    return {"response": result.get("final_response"), "draft": result.get("draft"), "events": result.get("calendar_events", [])}


@router.post("/stream")
async def stream_agent(
    request: AgentRequest,
    user_id: str = Depends(current_user_id),
    db: AsyncSession = Depends(db_session),
) -> StreamingResponse:
    async def events():
        graph = EmailAgent(db).compile()
        async for event in graph.astream_events(
            {"user_id": user_id, "message": request.message, "conversation_id": request.conversation_id, "errors": []},
            version="v2",
        ):
            if event["event"].endswith("_end"):
                yield f"data: {json.dumps({'type': event['event'], 'name': event.get('name'), 'data': event.get('data', {})}, default=str)}\n\n"
        yield "data: {\"type\":\"done\"}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
