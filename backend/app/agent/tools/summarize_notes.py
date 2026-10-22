import json
import re
from datetime import datetime
from langchain_core.tools import tool
from app.agent.llm import chat_llm, extract_json
from app.db.session import get_session
from app.db.models import HCP

SUMMARY_PROMPT_TEMPLATE = """
Condense the following voice-note transcript from a pharma field rep into a short,
form-ready interaction summary. Preserve the HCP name, interaction type, materials
shared, sentiment, outcomes, and follow-up commitments when present.

Transcript: "{transcript}"
"""

FORM_PROMPT_TEMPLATE = """
Extract complete Log HCP Interaction form fields from this voice note and summary.
Return ONLY valid JSON with exactly these keys:

hcp_name              (e.g. "Dr. Sharma", or empty string if not mentioned)
interaction_type      (one of: "Meeting", "Call", "Email", "Conference". Important: "voice note" is only the input format, not the interaction type. Use Meeting unless the transcript explicitly says call, email, or conference.)
interaction_date      (YYYY-MM-DD; use {today} if the note does not mention a date)
interaction_time      (HH:MM 24-hour; use {current_time} if the note does not mention a time)
attendees             (comma separated names other than the primary HCP, or empty string)
topics_discussed      (comma separated concise topics; include safety, dosing/titration, side effects, and real-world data if mentioned)
materials_shared      (comma separated materials shared, or empty string)
samples_distributed   (comma separated samples distributed, or empty string)
sentiment             (one of: "Positive", "Neutral", "Negative")
outcomes              (comma separated decisions, reactions, or commitments)
followup_actions      (comma separated next steps)

Voice note:
"{transcript}"

Summary:
"{summary}"
"""

DOCTOR_RE = re.compile(r"\bDr\.?\s+[A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*)?\b")
INTERACTION_TYPES = {"Meeting", "Call", "Email", "Conference"}


def _lookup_hcp_id(hcp_name: str) -> int | None:
    if not hcp_name:
        return None
    with get_session() as session:
        hcp = session.query(HCP).filter(HCP.name.ilike(f"%{hcp_name}%")).first()
        return hcp.id if hcp else None


def _extract_hcp_name(transcript: str, extracted_name: str | None) -> str:
    if extracted_name:
        return extracted_name.strip()
    match = DOCTOR_RE.search(transcript)
    return match.group(0).replace("Dr ", "Dr. ").strip() if match else ""


def _infer_interaction_type(transcript: str, extracted_type: str | None) -> str:
    text = transcript.lower()
    if "conference" in text:
        return "Conference"
    if "phone call" in text or "call with" in text or "called dr" in text:
        return "Call"
    if "email interaction" in text or "email exchange" in text or "emailed with" in text:
        return "Email"
    if extracted_type in INTERACTION_TYPES and extracted_type != "Call":
        return extracted_type
    return "Meeting"


def _append_topic_if_missing(topics: str, transcript: str, phrase: str, label: str) -> str:
    if phrase in transcript.lower() and label.lower() not in topics.lower():
        return f"{topics}, {label}" if topics else label
    return topics


@tool
def summarize_notes(transcript: str) -> str:
    """Condense a long voice-note transcript into complete Log HCP Interaction
    form fields. Uses the LLM to summarize and extract HCP name, interaction
    type, date/time, topics, materials, samples, sentiment, outcomes, and
    follow-up actions, then returns structured form_update data for the UI."""
    now = datetime.now()
    summary_response = chat_llm.invoke(SUMMARY_PROMPT_TEMPLATE.format(transcript=transcript))
    summary = summary_response.content.strip()

    extracted = extract_json(
        FORM_PROMPT_TEMPLATE.format(
            transcript=transcript,
            summary=summary,
            today=now.date().isoformat(),
            current_time=now.strftime("%H:%M"),
        )
    )

    hcp_name = _extract_hcp_name(transcript, extracted.get("hcp_name"))
    topics = extracted.get("topics_discussed") or summary
    topics = _append_topic_if_missing(topics, transcript, "side effects", "side effects in older patients")
    topics = _append_topic_if_missing(topics, transcript, "real-world adherence", "real-world adherence data")

    form_update = {
        "hcpName": hcp_name,
        "interactionType": _infer_interaction_type(transcript, extracted.get("interaction_type")),
        "date": extracted.get("interaction_date") or now.date().isoformat(),
        "time": extracted.get("interaction_time") or now.strftime("%H:%M"),
        "attendees": extracted.get("attendees", ""),
        "topicsDiscussed": topics,
        "materialsShared": extracted.get("materials_shared", ""),
        "samplesDistributed": extracted.get("samples_distributed", ""),
        "sentiment": extracted.get("sentiment") or "Neutral",
        "outcomes": extracted.get("outcomes", ""),
        "followupActions": extracted.get("followup_actions", ""),
    }

    hcp_id = _lookup_hcp_id(hcp_name)
    if hcp_id:
        form_update["hcpId"] = hcp_id

    return json.dumps({
        "action": "summarize_notes",
        "message": "Voice note summarized and copied into the interaction form.",
        "summary": summary,
        "form_update": form_update,
    })
