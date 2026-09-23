# backend/app/modules/leads/state_machine.py

import logging

logger = logging.getLogger(__name__)

VALID_TRANSITIONS = {
    "NEW":           {"ENGAGED", "HUMAN_HANDOFF"},
    "ENGAGED":       {"QUALIFYING", "HUMAN_HANDOFF", "NURTURE"},
    "QUALIFYING":    {"QUALIFIED", "NURTURE", "HUMAN_HANDOFF"},
    "QUALIFIED":     {"BOOKING", "NURTURE", "HUMAN_HANDOFF"},
    "BOOKING":       {"BOOKED", "HUMAN_HANDOFF", "NURTURE"},
    "BOOKED":        {"CLOSED", "HUMAN_HANDOFF"},
    "NURTURE":       {"ENGAGED", "QUALIFYING", "HUMAN_HANDOFF", "CLOSED"},
    "HUMAN_HANDOFF": {"ENGAGED", "QUALIFYING", "QUALIFIED", "BOOKING", "NURTURE", "CLOSED"},
    "CLOSED":        set(),
}


def can_transition(current_stage: str, requested_stage: str) -> bool:
    if current_stage == requested_stage:
        return True

    allowed = VALID_TRANSITIONS.get(current_stage, set())
    return requested_stage in allowed


def apply_lead_stage(lead, requested_stage: str) -> bool:
    if can_transition(lead.lead_stage, requested_stage):
        lead.lead_stage = requested_stage
        return True

    logger.warning(
        "Blocked invalid transition %s -> %s for lead %s",
        lead.lead_stage, requested_stage, lead.id
    )
    return False