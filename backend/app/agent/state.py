from typing import Annotated, Any, Optional, TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State passed through the LangGraph graph on every turn."""
    messages: Annotated[list, add_messages]
    hcp_id: Optional[int]
    current_interaction_id: Optional[int]
    current_form: Optional[dict[str, Any]]

