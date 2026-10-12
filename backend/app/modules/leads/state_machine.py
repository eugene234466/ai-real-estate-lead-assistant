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

# The stages a chat conversation moves through, in order.
# BOOKED is deliberately missing: only the appointments endpoint may set it.
CHAT_FLOW = ["NEW", "ENGAGED", "QUALIFYING", "QUALIFIED", "BOOKING"]


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


def has_qualification_data(lead) -> bool:
    # what "qualified" means: we know rent-or-buy, budget, and timeline
    return bool(lead.buy_or_rent) and lead.budget is not None and bool(lead.timeline)


def advance_lead_stage(lead, requested_stage: str) -> bool:
    """The AI suggests a stage; the server decides how far the lead actually moves.
    Returns True only if the lead ended up at the requested stage."""
    current = lead.lead_stage

    # BOOKED is only ever set by the appointments endpoint, never from chat
    if requested_stage == "BOOKED" and current != "BOOKED":
        requested_stage = "BOOKING"

    if requested_stage == current:
        return True

    # side exits (NURTURE, HUMAN_HANDOFF, CLOSED) and anything off the main path: one hop
    if current not in CHAT_FLOW or requested_stage not in CHAT_FLOW:
        return apply_lead_stage(lead, requested_stage)

    start = CHAT_FLOW.index(current)
    end = CHAT_FLOW.index(requested_stage)

    if end < start:
        logger.warning(
            "Ignored backwards stage change %s -> %s for lead %s",
            current, requested_stage, lead.id
        )
        return False

    # QUALIFIED and BOOKING are earned by the collected data, not the AI's say-so
    qualifying_index = CHAT_FLOW.index("QUALIFYING")
    if end > qualifying_index and not has_qualification_data(lead):
        logger.warning(
            "Held lead %s at or below QUALIFYING: %s requested but qualification data is incomplete",
            lead.id, requested_stage
        )
        end = max(start, qualifying_index)

    # check every hop first, so a rejected step never leaves a half-advanced lead
    path = CHAT_FLOW[start:end + 1]
    for step_from, step_to in zip(path, path[1:]):
        if not can_transition(step_from, step_to):
            logger.warning(
                "Blocked invalid transition %s -> %s for lead %s",
                step_from, step_to, lead.id
            )
            return False

    lead.lead_stage = CHAT_FLOW[end]
    return lead.lead_stage == requested_stage