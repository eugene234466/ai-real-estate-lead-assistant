# backend/app/modules/ai_engine/groq_client.py

import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def call_groq_chat(system_prompt: str, user_text: str) -> str:
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        temperature=0.2,
        response_format = {"type": "json_object"}
    )
    content = response.choices[0].message.content
    if content is None:
        return "Sorry, I couldn't generate a response right now."
    return content