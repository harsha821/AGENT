import json
from datetime import datetime
from langchain_core.tools import tool
from app.db.session import get_session
from app.db.models import Interaction, HCP
from app.agent.llm import extract_json

DIFF_PROMPT_TEMPLATE = """
A user wants to modify an already-logged HCP interaction. Given their instruction,
return ONLY valid JSON mapping field names to new values. Only include fields that
should change. Valid field names are exactly:
hcp_name, interaction_type, interaction_date, attendees, topics_discussed,
materials_shared, samples_distributed, sentiment, outcomes, followup_actions.

Use today's date ({today}) to resolve relative dates. Use ISO-8601 for interaction_date.
Instruction: "{instruction}"
"""


def _parse_interaction_date(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        if len(normalized) == 10:
            return datetime.fromisoformat(f"{normalized}T00:00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


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
def edit_interaction(interaction_id: int, instruction: str) -> str:
    """Modify a previously logged interaction using a natural language instruction,
    e.g. 'the name was actually Dr. John and sentiment was negative'. Uses the
    LLM to convert the instruction into a field/value diff and updates only
    those fields on the existing row. Returns structured form_update data for
    the UI."""
    prompt = DIFF_PROMPT_TEMPLATE.format(
        instruction=instruction,
        today=datetime.now().date().isoformat(),
    )
    diff = extract_json(prompt)

    if not diff:
        return json.dumps({
            "action": "edit_interaction",
            "message": f"Could not determine what to change for interaction #{interaction_id}.",
        })

    with get_session() as session:
        interaction = session.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return json.dumps({
                "action": "edit_interaction",
                "message": f"Interaction #{interaction_id} not found.",
            })

        changed_fields = []
        for field, value in diff.items():
            if field == "hcp_name":
                hcp = session.query(HCP).filter(HCP.name.ilike(f"%{value}%")).first()
                if not hcp:
                    hcp = HCP(name=str(value).strip(), specialty="")
                    session.add(hcp)
                    session.flush()
                interaction.hcp_id = hcp.id
                changed_fields.append("hcp_name")
            elif field == "interaction_date":
                parsed_date = _parse_interaction_date(value)
                if parsed_date:
                    interaction.interaction_date = parsed_date
                    changed_fields.append(field)
            elif hasattr(interaction, field):
                setattr(interaction, field, value)
                changed_fields.append(field)

        session.commit()
        session.refresh(interaction)
        hcp = session.query(HCP).filter(HCP.id == interaction.hcp_id).first()

        return json.dumps({
            "action": "edit_interaction",
            "message": f"Interaction updated successfully. Changed fields: {', '.join(changed_fields) or 'none'}.",
            "interaction_id": interaction.id,
            "form_update": _form_update(interaction, hcp),
        })
