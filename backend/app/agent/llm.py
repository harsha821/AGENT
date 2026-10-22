import json
from langchain_groq import ChatGroq
from app.config import settings

# Primary model per assignment spec. Swap to groq_fallback_model if gemma2-9b-it
# struggles with strict JSON extraction on your test data.
extraction_llm = ChatGroq(
    model=settings.groq_model,
    api_key=settings.groq_api_key,
    temperature=0,
)

chat_llm = ChatGroq(
    model=settings.groq_model,
    api_key=settings.groq_api_key,
    temperature=0.3,
)


def extract_json(prompt: str) -> dict:
    response = extraction_llm.invoke(prompt)

    text = response.content.strip()

    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()

    start = text.find("{")
    if start == -1:
        return {}

    decoder = json.JSONDecoder()

    try:
        obj, _ = decoder.raw_decode(text[start:])
        return obj
    except Exception:
        return {}