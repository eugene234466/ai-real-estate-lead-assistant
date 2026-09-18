# backend/app/modules/ai_engine/service.py

from app.modules.ai_engine.groq_client import call_groq_chat


def generate_ai_response(user_text: str) -> str:
    return call_groq_chat(user_text)