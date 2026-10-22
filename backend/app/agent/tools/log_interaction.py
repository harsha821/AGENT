import json
import re
from datetime import datetime
from langchain_core.tools import tool
from app.db.session import get_session
from app.db.models import Interaction, HCP
from app.agent.llm import extract_json

EXTRACTION_PROMPT_TEMPLATE = """
You are extracting structured data from a pharma field rep's freeform note about
a healthcare professional (HCP) interaction. Return ONLY valid JSON, no prose,
no markdown fences, with exactly these keys:

interaction_type     (one of: "Meeting", "Call", "Email", "Conference")
interaction_date     (ISO-8601 date or datetime. Resolve relative dates using today's date: {today})
attendees            (comma separated names, or empty string)
topics_discussed     (short text summary)
materials_shared     (comma separated list, or empty string)
samples_distributed  (comma separated list, or empty string)
sentiment            (one of: "Positive", "Neutral", "Negative")
outcomes             (short text summary of agreements/decisions)
followup_actions     (short text of next steps, or empty string)

Note: "{raw_text}"
"""

INTERACTION_TYPES = {"Meeting", "Call", "Email", "Conference"}


def _parse_interaction_date(value: str | None) -> datetime:
    if not value:
        return datetime.now()
    normalized = value.strip().replace("Z", "+00:00")
    try:
        if len(normalized) == 10:
            parsed_date = datetime.fromisoformat(f"{normalized}T00:00:00")
            now = datetime.now()
            return parsed_date.replace(hour=now.hour, minute=now.minute)
        return datetime.fromisoformat(normalized)
    except ValueError:
        return datetime.now()


def _infer_interaction_type(raw_text: str, extracted_type: str | None) -> str:
    text = raw_text.lower()
    if "conference" in text:
        return "Conference"
    if "phone call" in text or "call with" in text or "called dr" in text:
        return "Call"
    if "email" in text and not any(word in text for word in ["met", "meeting", "visited", "spoke"]):
        return "Email"
    if extracted_type in INTERACTION_TYPES:
        return extracted_type
    return "Meeting"


def _infer_sentiment(raw_text: str, extracted_sentiment: str | None) -> str:
    if extracted_sentiment in {"Positive", "Neutral", "Negative"}:
        return extracted_sentiment
    text = raw_text.lower()
    if "negative" in text or "not interested" in text or "concerned" in text:
        return "Negative"
    if "positive" in text or "optimistic" in text or "liked" in text:
        return "Positive"
    return "Neutral"


def _extract_after_keywords(raw_text: str, keywords: list[str]) -> str:
    text = raw_text.strip()
    for keyword in keywords:
        match = re.search(rf"{keyword}\s+([^.;]+)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def _fallback_topics(raw_text: str, extracted_topics: str | None) -> str:
    if extracted_topics:
        return extracted_topics
    discussed = _extract_after_keywords(raw_text, ["discussed", "talked about", "spoke about"])
    return discussed or raw_text


def _fallback_materials(raw_text: str, extracted_materials: str | None) -> str:
    if extracted_materials:
        return extracted_materials
    text = raw_text.lower()
    materials = []
    for label in ["brochure", "clinical summary", "dosing chart", "safety paper", "rwe paper", "clinical paper"]:
        if label in text:
            materials.append(label)
    return ", ".join(materials)


def _fallback_followups(raw_text: str, extracted_followups: str | None) -> str:
    if extracted_followups:
        return extracted_followups
    match = re.search(r"(?:follow up|send|share|provide)\s+([^.;]+)", raw_text, re.IGNORECASE)
    return match.group(0).strip() if match else ""


def _form_update(interaction: Interaction, hcp: HCP) -> dict:
    interaction_date = interaction.interaction_date or interaction.created_at or datetime.now()
    return {
        "currentInteractionId": interaction.id,
        "hcpId": hcp.id,
        "hcpName": hcp.name,
        "interactionType": interaction.interaction_type or "Meeting",
        "date": interaction_date.date().isoformat(),
        "time": interaction_date.strftime("%H:%M"),
        "attendees": interaction.attendees or "",
        "topicsDiscussed": interaction.topics_discussed or "",
        "materialsShared": interaction.materials_shared or "",
        "samplesDistributed": interaction.samples_distributed or "",
        "sentiment": interaction.sentiment or "Neutral",
        "outcomes": interaction.outcomes or "",
        "followupActions": interaction.followup_actions or "",
    }


@tool
def log_interaction(raw_text: str, hcp_name: str) -> str:
    """Capture a new HCP interaction from a freeform text note, given the
    HCP's name as it appears in the note (e.g. 'Dr. Rajesh Kumar'). This tool
    looks up the HCP internally - do NOT call search_hcp separately before
    this, and never pass a numeric hcp_id, only the name string. Uses the LLM
    to extract form fields, then persists a new row to the interactions table
    and returns structured form_update data for the UI."""
    with get_session() as session:
        hcp = session.query(HCP).filter(HCP.name.ilike(f"%{hcp_name}%")).first()
        if not hcp:
            hcp = HCP(name=hcp_name.strip(), specialty="")
            session.add(hcp)
            session.flush()

        prompt = EXTRACTION_PROMPT_TEMPLATE.format(
            raw_text=raw_text,
            today=datetime.now().date().isoformat(),
        )
        data = extract_json(prompt)

        interaction = Interaction(
            hcp_id=hcp.id,
            interaction_type=_infer_interaction_type(raw_text, data.get("interaction_type")),
            interaction_date=_parse_interaction_date(data.get("interaction_date")),
            attendees=data.get("attendees", ""),
            topics_discussed=_fallback_topics(raw_text, data.get("topics_discussed")),
            materials_shared=_fallback_materials(raw_text, data.get("materials_shared")),
            samples_distributed=data.get("samples_distributed", ""),
            sentiment=_infer_sentiment(raw_text, data.get("sentiment")),
            outcomes=data.get("outcomes", ""),
            followup_actions=_fallback_followups(raw_text, data.get("followup_actions")),
            created_via="chat",
        )
        session.add(interaction)
        session.commit()
        session.refresh(interaction)
        session.refresh(hcp)

        return json.dumps({
            "action": "log_interaction",
            "message": f"Interaction logged successfully for {hcp.name}.",
            "interaction_id": interaction.id,
            "form_update": _form_update(interaction, hcp),
        })
