from app.agent.tools.log_interaction import log_interaction
from app.agent.tools.edit_interaction import edit_interaction
from app.agent.tools.search_hcp import search_hcp
from app.agent.tools.summarize_notes import summarize_notes
from app.agent.tools.suggest_followups import suggest_followups
from app.agent.tools.get_latest_interaction import get_latest_interaction_by_hcp
from app.agent.tools.summarize_hcp_history import summarize_hcp_history

ALL_TOOLS = [
    log_interaction,
    edit_interaction,
    search_hcp,
    summarize_notes,
    suggest_followups,
    get_latest_interaction_by_hcp,
    summarize_hcp_history,
]
