# backend/app/modules/ai_engine/service.py

from app.modules.ai_engine.groq_client import call_groq_chat
from app.modules.properties.models import Property


def build_system_prompt(properties) -> str:
    property_lines = "\n".join(
        f"- {p.title}: {p.listing_type} for {p.price} {p.currency}/month, "
        f"{p.location}, {p.bedrooms} bed / {p.bathrooms} bath, "
        f"amenities: {', '.join(p.amenities or [])}, status: {p.availability_status}"
        for p in properties
    )

    return (
        "You are a helpful real estate assistant for Example Realty. "
        "Only use the verified property information below to answer questions. "
        "Never invent prices, availability, amenities, or details not listed here. "
        "If asked about something not covered, say you don't have that "
        "information available.\n\n"
        "Available properties:\n"
        f"{property_lines}"
    )


def generate_ai_response(user_text: str, organization_id) -> str:
    properties = Property.query.filter_by(organization_id=organization_id).all()

    system_prompt = build_system_prompt(properties)

    return call_groq_chat(system_prompt, user_text)