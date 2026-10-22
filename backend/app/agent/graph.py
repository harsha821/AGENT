import json
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage

from app.config import settings
from app.agent.state import AgentState
from app.agent.tools import ALL_TOOLS

SYSTEM_PROMPT = """
You are an AI assistant for a Pharma CRM. You control the interaction form by
calling LangGraph tools. The user must not manually fill the form.

Available tools:

- search_hcp
- log_interaction
- edit_interaction
- summarize_notes
- suggest_followups
- get_latest_interaction_by_hcp
- summarize_hcp_history

CRITICAL:

Only call the tool(s) required for the user's MOST RECENT request.
After successfully completing the requested task, respond with a short confirmation.
Do not call any additional tools after responding.
Do NOT continue calling unrelated tools.
Never invent IDs.
Never nest tool calls.
Always execute tools one at a time.

TOOL USAGE RULES

1. NEW INTERACTION

If the user describes a NEW meeting, call, email, visit or conference, ALWAYS
call log_interaction. This includes messages with words like met, visited,
spoke with, discussed, shared, samples, sentiment, outcome, agreed, or follow
up/next week when they are part of the meeting note.

Call log_interaction directly, passing the user's latest message as raw_text and
the HCP's name exactly as written (e.g. "Dr. Rajesh Kumar") in hcp_name. Do NOT
call search_hcp first for this case - log_interaction looks up or creates the
HCP itself.

Important: If a message says "I should follow up next week" or "promised to
send a paper next week" inside a new interaction note, that is still
log_interaction. Do NOT call suggest_followups for that.

2. EDIT CURRENT INTERACTION

If the user corrects or changes the currently displayed form (for example,
"Sorry, the name was actually Dr. John, and the sentiment was negative"), call
edit_interaction using the Current active interaction id from context. Pass the
user's latest message as instruction. Update only the fields requested by the
user and keep everything else unchanged.

If there is no current active interaction id and the user names an HCP, call
get_latest_interaction_by_hcp first, then edit_interaction.

3. SUMMARIZE INTERACTIONS

If the user asks to summarize interactions, call summarize_hcp_history.

4. FOLLOW-UP SUGGESTIONS

Only call suggest_followups when the user explicitly asks to suggest, generate,
or recommend follow-up actions. If the user is describing what they already
promised as part of a meeting note, use log_interaction instead.

If the user asks for follow-up suggestions for the current form and a current
active interaction id exists, call suggest_followups directly with that id. If
there is no current id but the user names an HCP, call get_latest_interaction_by_hcp,
then suggest_followups.

5. SUMMARIZE NOTES

If the user asks to summarize a pasted voice note or transcript into form-ready
notes, call summarize_notes.
"""

llm = ChatGroq(
    model=settings.groq_model,
    api_key=settings.groq_api_key,
    temperature=0.2,
)

llm_with_tools = llm.bind_tools(ALL_TOOLS)


def _context_prompt(state: AgentState) -> str:
    context = {
        "hcp_id": state.get("hcp_id"),
        "current_interaction_id": state.get("current_interaction_id"),
        "current_form": state.get("current_form") or {},
    }
    return (
        "Current CRM context for this request. Use it only to choose tool "
        "arguments; do not treat it as the user's note.\n"
        f"{json.dumps(context, default=str)}"
    )


def agent_node(state: AgentState):
    print("\n================ AGENT NODE ================")

    for msg in state["messages"]:
        print(f"{msg.type}: {msg.content}")

    non_system_messages = [msg for msg in state["messages"] if msg.type != "system"]
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        SystemMessage(content=_context_prompt(state)),
    ] + non_system_messages

    response = llm_with_tools.invoke(messages)

    print("\n================ AGENT RESPONSE ================")
    print(response)

    return {"messages": [response]}


graph = StateGraph(AgentState)

graph.add_node("agent", agent_node)
graph.add_node("tools", ToolNode(ALL_TOOLS))

graph.set_entry_point("agent")

graph.add_conditional_edges(
    "agent",
    tools_condition,
    {
        "tools": "tools",
        END: END,
    },
)

graph.add_edge("tools", "agent")

app_graph = graph.compile()

