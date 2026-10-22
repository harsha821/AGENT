import json
import re
from fastapi import APIRouter, HTTPException
from groq import RateLimitError
from langchain_core.messages import HumanMessage

from app.schemas import ChatRequest, ChatResponse
from app.agent.graph import app_graph
from app.db.session import get_session
from app.db.models import HCP

router = APIRouter(
    prefix="/agent",
    tags=["agent"],
)

DOCTOR_RE = re.compile(r"\bDr\.?\s+[A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*)?\b")


def _parse_json_content(content):
    if not isinstance(content, str):
        return None
    text = content.strip()
    if not text.startswith("{"):
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _extract_tool_result(messages):
    latest_payload = None
    for message in messages:
        if getattr(message, "type", None) != "tool":
            continue

        content = getattr(message, "content", "")
        if isinstance(content, dict):
            payload = content
        elif isinstance(content, str):
            payload = _parse_json_content(content)
            if payload is None:
                payload = content.strip() or None
        else:
            payload = None

        if payload is not None:
            latest_payload = payload
    return latest_payload or {}


def _format_tool_response(tool_result, fallback_text: str) -> str:
    if isinstance(tool_result, str):
        return tool_result.strip() or fallback_text

    if isinstance(tool_result, dict):
        if tool_result.get("action") == "suggest_followups":
            followup_text = (
                (tool_result.get("form_update") or {}).get("followupActions")
                if isinstance(tool_result.get("form_update"), dict)
                else None
            )
            if followup_text:
                return str(followup_text)

        if tool_result.get("message") and tool_result.get("action") != "suggest_followups":
            return str(tool_result["message"])

        if tool_result.get("found") is False:
            return tool_result.get("message") or "No HCP found."

        if tool_result.get("found") is True:
            lines = [
                "🔍 HCP Found",
                f"Name: {tool_result.get('name', '')}",
                f"Specialty: {tool_result.get('specialty', '')}",
                f"HCP ID: {tool_result.get('hcp_id', '')}",
            ]
            return "\n".join(line for line in lines if not line.endswith(": "))

    if fallback_text:
        return fallback_text

    return "Done."


def _extract_hcp_name(message: str) -> str:
    match = DOCTOR_RE.search(message or "")
    if not match:
        return ""
    return match.group(0).replace("Dr ", "Dr. ").strip()


def _lookup_hcp_id(hcp_name: str):
    if not hcp_name:
        return None
    with get_session() as session:
        hcp = session.query(HCP).filter(HCP.name.ilike(f"%{hcp_name}%")).first()
        return hcp.id if hcp else None


def _repair_form_update(form_update, original_message: str):
    if not form_update:
        return form_update

    if not form_update.get("hcpName"):
        hcp_name = _extract_hcp_name(original_message)
        if hcp_name:
            form_update["hcpName"] = hcp_name
            hcp_id = _lookup_hcp_id(hcp_name)
            if hcp_id:
                form_update["hcpId"] = hcp_id

    return form_update


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    """
    Single entry point for the conversational AI assistant.

    The LangGraph agent automatically decides which tool(s) to use:
    - search_hcp
    - log_interaction
    - edit_interaction
    - summarize_notes
    - suggest_followups
    - get_latest_interaction_by_hcp
    - summarize_hcp_history
    """

    initial_state = {
        "messages": [
            HumanMessage(content=payload.message)
        ],
        "hcp_id": payload.hcp_id,
        "current_interaction_id": payload.current_interaction_id,
        "current_form": payload.current_form or {},
    }

    try:
        result = app_graph.invoke(
            initial_state,
            config={"recursion_limit": 12}
        )

        final_message = result["messages"][-1]
        tool_result = _extract_tool_result(result["messages"])
        response_text = _format_tool_response(tool_result, final_message.content or "Done.")
        form_update = _repair_form_update(
            tool_result.get("form_update") if isinstance(tool_result, dict) else None,
            payload.message,
        )

        parsed_final = _parse_json_content(response_text)
        if parsed_final and parsed_final.get("message"):
            response_text = parsed_final["message"]

        return ChatResponse(
            response=response_text,
            form_update=form_update,
        )

    except RateLimitError:
        raise HTTPException(
            status_code=429,
            detail="Groq API rate limit exceeded. Please wait 10-15 seconds and try again."
        )

    except Exception as e:
        print("Agent Error:", e)  # Prints full error in terminal

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
