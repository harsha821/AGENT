from langchain_core.tools import tool
from app.db.session import get_session
from app.db.models import HCP


@tool
def search_hcp(name_query: str) -> dict:
    """
    Find an HCP by name and return structured data.
    """
    print(f"\nsearch_hcp called with: {name_query}")
    with get_session() as session:
        match = (
            session.query(HCP)
            .filter(HCP.name.ilike(f"%{name_query}%"))
            .first()
        )

        if not match:
            return {
                "found": False,
                "message": f"No HCP found matching '{name_query}'."
            }

        return {
            "found": True,
            "hcp_id": match.id,
            "name": match.name,
            "specialty": match.specialty,
        }