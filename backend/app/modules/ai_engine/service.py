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
        f"""You are an AI real estate assistant for Example Realty.
           Use ONLY the verified property information below. NEVER invent
           prices, availability, amenities, or details not listed here.
           
           Available properties:
           " + {property_lines} + "
           
           You must respond with a single JSOn object matching EXACTLY this shape, and
           nothing else (no markdown, no extra text):
           
           {{
               "intent": "property_inquiry" | "general_question" | "unclear",
                "property_id": string or null,
                "buy_or_rent": "buy" | "rent" | null,
                "budget": number or null,
                "timeline": string or null,
                "missing_information": [string, ...],
                "lead_stage": one of "NEW" | "ENGAGED" | "QUALIFYING" | "QUALIFIED" |
                                "BOOKING" | "BOOKED" | "NURTURE" | "HUMAN_HANDOFF" | "CLOSED",
                "next_action": string,
                "human_handoff_required": true | false,
                "response": string  // the natural-language reply to show the lead 
           }}
           
           Ask only ONE qualifying question at a time in the 'response' field.
           Progress lead_stage forward only when approprite based on the conversation.
        """          
    )    


def generate_ai_response(user_text: str, organization_id) -> str:
    properties = Property.query.filter_by(organization_id=organization_id).all()

    system_prompt = build_system_prompt(properties)

    return call_groq_chat(system_prompt, user_text)