# AI-First CRM — HCP Module: Log Interaction Screen

An AI-first CRM module for pharma field representatives to log Healthcare
Professional (HCP) interactions, either through a **structured form** or a
**conversational chat interface** powered by a LangGraph agent running on
Groq.

## Architecture

```
React (Redux) UI  ──┬── structured form ──▶  FastAPI  /interactions  ──▶ Postgres
                     └── chat message   ──▶  FastAPI  /agent/chat    ──▶ LangGraph agent ──▶ Groq LLM
                                                                              │
                                                                              ▼
                                                                    7 LangGraph tools (DB read/write)
```

Both the structured form and the AI chat interface persist data to the same
`interactions` table, ensuring consistent storage regardless of how the
interaction is logged.

## AI-Powered Form Filling

The AI Assistant extracts structured information from natural language and
uses LangGraph tools to create or update interaction records. The user
interacts with the AI conversationally instead of manually editing the
interaction details field by field.

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React + Redux Toolkit, Google Inter font |
| Backend | Python, FastAPI |
| AI agent framework | LangGraph |
| LLM | Groq `llama-3.1-8b-instant` (primary) — `llama-3.3-70b-versatile` and `gemma2-9b-it` also supported via `GROQ_MODEL` env var |
| Database | PostgreSQL |

## LangGraph agent

The agent is a single `StateGraph` with two nodes: `agent` (the LLM bound to
tools) and `tools` (a `ToolNode` executing whichever tool the LLM picks). The
graph loops `agent → tools → agent` until the LLM responds without a tool
call, then returns to the user. Its role is to translate a rep's freeform
note or instruction into structured CRM actions — deciding which tool(s) to
call, and calling only the tool(s) needed for what the user's message
actually asks.

### Implemented LangGraph Tools

The assignment requires a minimum of five LangGraph tools. This project
implements seven tools in total, including two helper tools used internally
by the agent to improve reliability and prevent invalid tool calls.

1. **`log_interaction`** — Captures a new interaction from freeform text,
   given the HCP's name as written in the note. Looks up the HCP internally,
   calls the LLM with an extraction prompt to pull `interaction_type`,
   `topics_discussed`, `materials_shared`, `samples_distributed`,
   `sentiment`, `outcomes`, and `followup_actions` out of the note as JSON,
   then inserts a row into the `interactions` table.
2. **`edit_interaction`** — Modifies an already-logged interaction using a
   natural-language instruction (e.g. "change sentiment to positive"). The
   LLM converts the instruction into a field/value diff, and only those
   fields are updated on the existing row.
3. **`search_hcp`** — Searches for a Healthcare Professional by name and
   returns the HCP ID, name, and specialty so other tools can reference the
   correct record.
4. **`summarize_notes`** — Condenses a long, pasted voice-note transcript
   into concise "Topics Discussed" / "Outcomes" text (mirrors the
   "Summarize from Voice Note" button in the UI mockup).
5. **`suggest_followups`** — Given a logged interaction, generates 2–3
   follow-up action suggestions, saves them to the interaction's
   `followup_actions` field, and returns them to the AI Assistant chat.
6. **`get_latest_interaction_by_hcp`** — Resolves references like "my last
   meeting with Dr. Smith" into a real `interaction_id`, used internally
   before `edit_interaction` or `suggest_followups` so the agent never has
   to guess an ID.
7. **`summarize_hcp_history`** — Summarizes *all* logged interactions with a
   given HCP (sentiment trend, recurring topics, open follow-ups) — distinct
   from `summarize_notes`, which only condenses a single pasted transcript.

## Setup & running locally

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL running locally
- A Groq API key from https://console.groq.com/keys

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and paste your GROQ_API_KEY + DATABASE_URL

uvicorn app.main:app --reload --port 8000
```

The app auto-creates tables on startup (`init_db()`). Seed a few test HCPs by
running the inserts in `app/db/schema.sql` against your database, or insert
them via `psql`/pgAdmin.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`. The app expects the backend at
`http://localhost:8000` (see `src/api/client.js`).

## Project structure

```
hcp-crm/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI entry point, CORS, router mounting
│   │   ├── config.py              # env-driven settings
│   │   ├── schemas.py             # Pydantic request/response models
│   │   ├── db/
│   │   │   ├── models.py          # SQLAlchemy models (HCP, Interaction)
│   │   │   ├── session.py         # engine/session + init_db()
│   │   │   └── schema.sql         # reference SQL + seed data
│   │   ├── routers/
│   │   │   ├── interactions.py    # structured form CRUD
│   │   │   └── agent.py           # /agent/chat endpoint
│   │   └── agent/
│   │       ├── state.py           # AgentState (messages, hcp_id)
│   │       ├── llm.py             # shared Groq client + JSON extraction helper
│   │       ├── graph.py           # LangGraph StateGraph wiring + system prompt
│   │       └── tools/             # all 7 tools, one file each
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # combines form + chat panels
│   │   ├── components/
│   │   │   ├── InteractionForm.jsx
│   │   │   ├── ChatPanel.jsx
│   │   │   └── FollowUpSuggestions.jsx
│   │   ├── redux/                  # store + interactionSlice
│   │   └── api/client.js           # axios wrapper
│   └── package.json
```

## Demo workflow

1. **Log Interaction** — e.g. *"Met Dr. Rajesh Kumar today. Discussed
   NeuroCare Plus. Positive response."*
2. **Edit Interaction** — e.g. *"Change the sentiment to Neutral."*
3. **Search HCP** — e.g. *"Find Dr. Rajesh Kumar."*
4. **Summarize Interaction History** — e.g. *"Summarize my interactions
   with Dr. Rajesh Kumar."*
5. **Suggest Follow-ups** — e.g. *"Suggest follow-up actions for my last
   meeting with Dr. Rajesh Kumar."*

All actions are orchestrated by a LangGraph agent running on Groq, which
selects and executes the appropriate tool(s) based on the user's natural
language request.

## Design notes / known limitations

- The default model is `llama-3.1-8b-instant` for speed; `GROQ_MODEL` can be
  swapped to `llama-3.3-70b-versatile` for more reliable JSON extraction if
  needed, or `gemma2-9b-it` per the original spec.
- During development, two design challenges influenced the final
  implementation: (1) Groq occasionally issues parallel tool calls before an
  earlier one's result is available, so `log_interaction` resolves the HCP
  name internally rather than depending on a prior `search_hcp` call; (2)
  natural references like "my last meeting with Dr. X" have no numeric ID,
  so `get_latest_interaction_by_hcp` was added to resolve them safely
  instead of letting the model invent one.
- The chat panel and form panel share Redux state but are not yet
  auto-synced after a chat-side log.
- Authentication/authorization is out of scope for this assignment and not
  implemented.
- Voice note upload/consent flow is stubbed as a text transcript input to
  `summarize_notes` rather than an actual audio pipeline.