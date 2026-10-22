import unittest
from unittest.mock import patch, MagicMock

import app.routers.agent as agent_router
from app.schemas import ChatRequest


class AgentRouterTests(unittest.TestCase):
    def test_chat_prefers_tool_result_message(self):
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = {
            "messages": [
                type("Message", (), {"type": "ai", "content": "assistant final"})(),
                type("Message", (), {"type": "tool", "content": '{"message": "Tool summary"}'})(),
            ]
        }

        with patch.object(agent_router, "app_graph", mock_graph):
            response = agent_router.chat(ChatRequest(message="Summarize my interactions with Dr. Smith"))

        self.assertEqual(response.response, "Tool summary")
        self.assertIsNone(response.form_update)

    def test_chat_formats_search_tool_output(self):
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = {
            "messages": [
                type("Message", (), {"type": "ai", "content": "assistant final"})(),
                type("Message", (), {
                    "type": "tool",
                    "content": {
                        "found": True,
                        "hcp_id": 1,
                        "name": "Dr. Smith",
                        "specialty": "Oncology",
                    },
                })(),
            ]
        }

        with patch.object(agent_router, "app_graph", mock_graph):
            response = agent_router.chat(ChatRequest(message="Find Dr. Smith"))

        self.assertIn("🔍 HCP Found", response.response)
        self.assertIn("Name: Dr. Smith", response.response)


if __name__ == "__main__":
    unittest.main()
