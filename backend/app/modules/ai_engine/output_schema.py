import json

VALID_LEAD_STAGES = {"NEW", "ENGAGED", "QUALIFYING","QUALIFIED",
    "BOOKING", "BOOKED", "NURTURE", "HUMAN_HANDOFF", "CLOSED"}

VALID_BUY_OR_RENT = {"buy", "rent", None}
REQUIRED_FIELDS = ["intent", "property_id", "buy_or_rent", "budget", "timeline",
        "missing_information", "lead_stage", "next_action", "human_handoff_required", "response"]


def validate_ai_output(raw_text):
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        return(False, None, 'not valid JSON')
    
    for field in REQUIRED_FIELDS:
        if field not in parsed:
            return(False, None, f"missing field: {field}")
    
    if parsed['lead_stage'] not in VALID_LEAD_STAGES:
        return(False, None, "invalid lead_stage")
    
    if parsed['buy_or_rent'] not in VALID_BUY_OR_RENT:
        return(False, None, "invalid buy_or-rent")
    
    if type(parsed['human_handoff_required']) is not bool:
        return(False, None, "invalid human_handoff_required")
    
    return(True, parsed, None)