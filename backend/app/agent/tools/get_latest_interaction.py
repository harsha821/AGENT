from langchain_core.tools import tool
from app.db.session import get_session
from app.db.models import Interaction, HCP


@tool
def get_latest_interaction_by_hcp(hcp_name: str) -> str:
    """Find the most recent logged interaction for a given HCP by name (e.g.
    'Dr. Smith'). Use this whenever the user refers to an interaction by
    description ('my last meeting with Dr. Smith', 'the interaction with
    Dr. Sharma') instead of giving a numeric interaction_id directly. Returns
    the real interaction_id plus a short summary, so it can be passed to
    edit_interaction or suggest_followups. Never invent or guess an
    interaction_id - always call this tool first to get the real one."""
    with get_session() as session:
        hcp = session.query(HCP).filter(HCP.name.ilike(f"%{hcp_name}%")).first()
        if not hcp:
            return f"No HCP found matching '{hcp_name}'."

        interaction = (
            session.query(Interaction)
            .filter(Interaction.hcp_id == hcp.id)
            .order_by(Interaction.created_at.desc())
            .first()
        )
        if not interaction:
            return f"No interactions logged yet for {hcp.name}."

        return (
            f"interaction_id={interaction.id}, hcp={hcp.name}, "
            f"type={interaction.interaction_type}, sentiment={interaction.sentiment}, "
            f"topics={interaction.topics_discussed}"
        )