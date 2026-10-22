import json
from langchain_core.tools import tool
from app.db.session import get_session
from app.db.models import Interaction
from app.agent.llm import chat_llm

SUGGEST_PROMPT_TEMPLATE = """
Based on this logged HCP interaction, suggest 2-3 concrete follow-up actions
for the field rep. Keep each suggestion to one short line. Format as a
bulleted list with "- " prefixes, nothing else.

Interaction type: {interaction_type}
Topics discussed: {topics_discussed}
Sentiment: {sentiment}
Outcomes: {outcomes}
"""


@tool
def suggest_followups(interaction_id: int) -> str:
    """Given a logged interaction, generate 2-3 AI-suggested follow-up actions
    (e.g. 'Schedule follow-up meeting in 2 weeks', 'Send Phase III PDF'),
    persist them to the interaction, and return structured form_update data for
    the UI follow-up field."""
    with get_session() as session:
        interaction = session.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return json.dumps({
                "action": "suggest_followups",
                "message": f"Interaction #{interaction_id} not found.",
            })

        prompt = SUGGEST_PROMPT_TEMPLATE.format(
            interaction_type=interaction.interaction_type or "Meeting",
            topics_discussed=interaction.topics_discussed or "",
            sentiment=interaction.sentiment or "Neutral",
            outcomes=interaction.outcomes or "",
        )
        response = chat_llm.invoke(prompt)
        suggestions = response.content.strip()

        interaction.followup_actions = suggestions
        session.commit()
        return json.dumps({
            "action": "suggest_followups",
            "message": "Follow-up suggestions added successfully.",
            "interaction_id": interaction.id,
            "form_update": {
                "followupActions": suggestions,
            },
        })
