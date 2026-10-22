"""
Quick manual test script - run this to exercise all 5 LangGraph tools end to
end before recording the demo video.

Usage:
    cd backend
    python test_agent.py
"""
from langchain_core.messages import HumanMessage
from app.agent.graph import app_graph
from app.db.session import init_db


def run(message: str):
    print(f"\n>>> USER: {message}")
    result = app_graph.invoke({"messages": [HumanMessage(content=message)], "hcp_id": None})
    print(f"<<< AGENT: {result['messages'][-1].content}")


if __name__ == "__main__":
    init_db()

    # 1. search_hcp
    run("Find Dr. Smith in our HCP list.")

    # 2. log_interaction (also exercises search_hcp implicitly)
    run(
        "Log an interaction: met Dr. Smith today, discussed Product X efficacy "
        "data, he seemed positive, shared the oncology brochure."
    )

    # 3. edit_interaction
    run("For interaction 1, change the sentiment to Neutral.")

    # 4. summarize_notes
    run(
        "Summarize this voice note: 'So I sat down with Dr. Sharma for about "
        "twenty minutes, we went over the new cardiology trial results, she "
        "asked a lot of questions about side effects, seemed cautiously "
        "optimistic, agreed to review the full study and get back to us next "
        "week.'"
    )

    # 5. suggest_followups
    run("Suggest follow-up actions for interaction 1.")
