# backend/app/modules/ai_engine/service.py

from app.modules.ai_engine.groq_client import call_groq_chat
from app.modules.ai_engine.output_schema import validate_ai_output
from app.modules.properties.models import Property
import logging

logger = logging.getLogger(__name__)

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


def generate_ai_response(user_text: str, organization_id):
    properties = Property.query.filter_by(organization_id = organization_id).all()

    system_prompt = build_system_prompt(properties)

    raw_output = call_groq_chat(system_prompt, user_text)
    is_valid, parsed, error = validate_ai_output(raw_output)
   
    if not is_valid:
        logger.error("Invalid AI output: %s", error)
        return {
            "intent": None,
            "property_id": None,
            "buy_or_rent": None,
            "budget": None,
            "timeline": None,
            "missing_information": [],
            "lead_stage": "HUMAN_HANDOFF",
            "next_action": "ESCALATE_TO_AGENT",
            "human_handoff_required": True,
            "response": "Sorry, I'm having trouble processing that right now. Let me get an agent to help."
    }
        
    return parsed
            