from langchain_core.tools import tool
from app.db.session import get_session
from app.db.models import Interaction, HCP
from app.agent.llm import chat_llm

SUMMARY_PROMPT_TEMPLATE = """
Summarize this field rep's interaction history with an HCP in 3-4 sentences.
Mention the number of interactions, overall sentiment trend, and any
recurring topics or open follow-ups.

Interactions:
{interaction_list}
"""


@tool
def summarize_hcp_history(hcp_name: str) -> str:
    """Summarize all logged interactions with a given HCP by name, e.g.
    'summarize my interactions with Dr. Smith'. Pulls every interaction row
    for that HCP from the database and asks the LLM to produce a short
    narrative summary covering sentiment trend, recurring topics, and open
    follow-ups. Different from summarize_notes, which condenses a single
    pasted voice-note transcript rather than database history."""
    with get_session() as session:
        hcp = session.query(HCP).filter(HCP.name.ilike(f"%{hcp_name}%")).first()
        if not hcp:
            return f"No HCP found matching '{hcp_name}'."

        interactions = (
            session.query(Interaction)
            .filter(Interaction.hcp_id == hcp.id)
            .order_by(Interaction.created_at.asc())
            .all()
        )
        if not interactions:
            return f"No interactions logged yet for {hcp.name}."

        lines = [
            f"- {i.interaction_date or i.created_at}: type={i.interaction_type}, "
            f"sentiment={i.sentiment}, topics={i.topics_discussed}, outcomes={i.outcomes}"
            for i in interactions
        ]
        prompt = SUMMARY_PROMPT_TEMPLATE.format(interaction_list="\n".join(lines))
        response = chat_llm.invoke(prompt)
        return response.content.strip()