# backend/app/modules/conversations/routes.py

from datetime import datetime, timezone
import logging
import uuid

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt

from app.extensions import db
from app.modules.conversations.models import Conversation, Message
from app.modules.organizations.models import Organization
from app.modules.properties.models import Property
from app.modules.leads.models import Lead
from app.modules.leads.state_machine import advance_lead_stage
from app.modules.ai_engine.service import generate_ai_response
from app.modules.notifications.models import Notification

logger = logging.getLogger(__name__)

conversations_bp = Blueprint('conversations', __name__)

MAX_MESSAGE_LENGTH = 1000
MAX_HISTORY_MESSAGES = 10
MAX_POLL_MESSAGES = 50
FALLBACK_REPLY = "Sorry, I'm having trouble right now. An agent will follow up with you shortly."
PHONE_REJECTED_REPLY = "That number looks incomplete. Could you double-check it for me?"


# ---------- helpers ----------

def is_valid_uuid(value):
    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False


def clean_budget(value):
    try:
        budget = float(value)
    except (TypeError, ValueError):
        return None
    if budget < 0 or budget >= 10**10:
        return None
    return budget


def clean_text(value, max_length):
    if value is None:
        return None
    return str(value)[:max_length]


def clean_phone(value):
    if not isinstance(value, str):
        return None
    value = value.strip()
    digits = "".join(ch for ch in value if ch.isdigit())
    # Ghanaian local numbers are 10 digits starting with 0
    if digits.startswith("0") and len(digits) != 10:
        return None
    cleaned = ("+" if value.startswith("+") else "") + digits
    # reject instead of truncating: a cut-off phone number is worse than none
    return cleaned if 7 <= len(cleaned) <= 13 else None


def clean_email(value):
    if not isinstance(value, str):
        return None
    value = value.strip()
    if len(value) > 255 or " " in value or value.count("@") != 1:
        return None
    local, domain = value.split("@")
    if not local or "." not in domain:
        return None
    return value


def can_reach(lead):
    # an agent can follow up only if we have a name and at least one way to contact them
    return bool(lead.name and (lead.phone or lead.email))


# ---------- public: the visitor-facing chat widget ----------

@conversations_bp.route('/message', methods=['POST'])
def send_message():
    body = request.get_json(silent=True) or {}
    text = body.get('text')
    widget_key = body.get('widget_key')
    public_token = body.get('conversation_token')

    if not isinstance(text, str) or not text.strip() or not widget_key:
        return jsonify({"error": "text and widget_key are required"}), 400

    if len(text) > MAX_MESSAGE_LENGTH:
        return jsonify({"error": "message too long"}), 400

    user_text = text.strip()

    # org comes from the widget key, never from anything else the client sends
    org = Organization.query.filter_by(widget_key=str(widget_key)).first()
    if not org:
        return jsonify({"error": "not found"}), 404

    # each visitor gets their own conversation, found by an unguessable token
    if public_token:
        conversation = Conversation.query.filter_by(
            public_token=str(public_token),
            organization_id=org.id
        ).first()
        if not conversation:
            return jsonify({"error": "not found"}), 404
    else:
        conversation = Conversation(organization_id=org.id)
        db.session.add(conversation)
        db.session.commit()

    user_message = Message(
        organization_id=org.id,
        conversation_id=conversation.id,
        sender="user",
        text=user_text
    )
    db.session.add(user_message)
    db.session.commit()

    if not conversation.ai_enabled:
        return jsonify({
            "reply": None,
            "ai_paused": True,
            "message": "This conversation is currently being handled by an agent.",
            "conversation_token": conversation.public_token,
            "user_message_id": str(user_message.id)                      # NEW
        })

    # what the AI needs to stay coherent: the recent transcript and what we know so far
    recent = (
        Message.query
        .filter(
            Message.conversation_id == conversation.id,
            Message.organization_id == org.id,
            Message.id != user_message.id      # the current message is passed separately
        )
        .order_by(Message.created_at.desc())
        .limit(MAX_HISTORY_MESSAGES)
        .all()
    )
    history = [(m.sender, m.text) for m in reversed(recent)]   # oldest first

    lead = None
    if conversation.lead_id is not None:
        lead = Lead.query.filter_by(
            id=conversation.lead_id, organization_id=org.id
        ).first()

    try:
        ai_result = generate_ai_response(user_text, org.id, history=history, lead=lead)
    except Exception:
        logger.exception("AI generation failed for conversation %s", conversation.id)
        return jsonify({"error": "The assistant is unavailable right now. Please try again."}), 503

    if lead is None:
        lead = Lead(organization_id=org.id, source="web_chat")
        db.session.add(lead)
        db.session.flush()
        conversation.lead_id = lead.id

    # remember whether we could already reach this visitor, before saving anything
    had_contact = can_reach(lead)

    # the AI's output is untrusted: validate every field before it touches the DB
    property_id = ai_result.get('property_id')
    if property_id and is_valid_uuid(property_id):
        prop = Property.query.filter_by(
            id=str(property_id), organization_id=org.id
        ).first()
        if prop:
            lead.property_id = prop.id

    if ai_result.get('buy_or_rent') is not None:
        lead.buy_or_rent = ai_result['buy_or_rent']

    if ai_result.get('location_preference') is not None:
        lead.location_preference = clean_text(ai_result['location_preference'], 500)

    budget = clean_budget(ai_result.get('budget'))
    if budget is not None:
        lead.budget = budget

    if ai_result.get('timeline') is not None:
        lead.timeline = clean_text(ai_result['timeline'], 200)

    if ai_result.get('intent') is not None:
        lead.intent = clean_text(ai_result['intent'], 500)

    name = ai_result.get('name')
    if isinstance(name, str) and name.strip():
        lead.name = name.strip()[:255]

    # remember when the visitor gave a number that failed the check
    raw_phone = ai_result.get('phone')
    phone = clean_phone(raw_phone)
    phone_rejected = isinstance(raw_phone, str) and bool(raw_phone.strip()) and phone is None
    if phone:
        lead.phone = phone

    email = clean_email(ai_result.get('email'))
    if email:
        lead.email = email

    handoff_required = bool(ai_result.get("human_handoff_required"))

    # the AI suggests a stage; the server decides how far the lead actually moves
    advance_lead_stage(lead, ai_result["lead_stage"])

    # keep the lead's stage and the AI on/off switch consistent
    if lead.lead_stage == "HUMAN_HANDOFF":
        handoff_required = True

    # the server enforces what the reply promises: once an agent can reach the
    # visitor, an agent gets notified, whatever the model's flag says
    contact_just_collected = (not had_contact) and can_reach(lead)
    if contact_just_collected:
        if not handoff_required:
            logger.info("Server forced handoff: contact details collected for lead %s", lead.id)
        handoff_required = True

    lead.last_contact_at = datetime.now(timezone.utc).replace(tzinfo=None)

    reply_text = ai_result.get("response")
    if not isinstance(reply_text, str) or not reply_text.strip():
        reply_text = FALLBACK_REPLY
        handoff_required = True

    # a rejected number would make "an agent will contact you" untrue, so keep
    # the chat live and ask for the number again
    if phone_rejected and not can_reach(lead):
        logger.info("Rejected an invalid phone number for lead %s", lead.id)
        reply_text = PHONE_REJECTED_REPLY
        if lead.lead_stage != "HUMAN_HANDOFF":
            handoff_required = False

    if handoff_required:
        conversation.ai_enabled = False

        viewing = ai_result.get('viewing_preference')
        if isinstance(viewing, str) and viewing.strip():
            note = f"Viewing requested for: {viewing.strip()[:200]} - lead stage: {lead.lead_stage}"
        elif contact_just_collected:
            # deliberately no phone or email here: contact details live on the lead only
            note = f"Visitor left contact details for follow-up - lead stage: {lead.lead_stage}"
        else:
            note = f"Conversation needs human attention - lead stage: {lead.lead_stage}"

        db.session.add(Notification(
            organization_id=org.id,
            lead_id=lead.id,
            conversation_id=conversation.id,
            type="HUMAN_HANDOFF",
            message=note
        ))

    ai_message = Message(                                                # NEW: named, so its id can be returned
        organization_id=org.id,
        conversation_id=conversation.id,
        sender="ai",
        text=reply_text
    )
    db.session.add(ai_message)

    try:
        db.session.commit()  # lead update, handoff, notification, and reply land together
    except Exception:
        db.session.rollback()
        logger.exception("Failed to save AI reply for conversation %s", conversation.id)
        return jsonify({"error": "Could not save the reply. Please try again."}), 500

    return jsonify({
        "reply": reply_text,
        "ai_paused": not conversation.ai_enabled,
        "conversation_token": conversation.public_token,
        "user_message_id": str(user_message.id),                         # NEW
        "reply_id": str(ai_message.id),                                  # NEW
    })


# NEW: the widget polls this for agent replies, follow-ups, and to reload after a refresh
@conversations_bp.route('/poll', methods=['POST'])
def poll_messages():
    body = request.get_json(silent=True) or {}
    widget_key = body.get('widget_key')
    public_token = body.get('conversation_token')
    after_raw = body.get('after')

    if not widget_key or not public_token:
        return jsonify({"error": "widget_key and conversation_token are required"}), 400

    org = Organization.query.filter_by(widget_key=str(widget_key)).first()
    if not org:
        return jsonify({"error": "not found"}), 404

    # the token lookup also filters on the org, so a token from one agency
    # can't be used through another agency's widget key
    conversation = Conversation.query.filter_by(
        public_token=str(public_token),
        organization_id=org.id
    ).first()
    if not conversation:
        return jsonify({"error": "not found"}), 404

    after = None
    if after_raw:
        try:
            after = datetime.fromisoformat(str(after_raw))
        except ValueError:
            return jsonify({"error": "after must be an ISO datetime"}), 400
        if after.tzinfo is not None:
            after = after.astimezone(timezone.utc).replace(tzinfo=None)

    query = Message.query.filter_by(
        conversation_id=conversation.id, organization_id=org.id
    )
    if after is not None:
        # >= so a message saved in the same instant as the last one is never skipped;
        # the widget ignores repeats by message id
        query = query.filter(Message.created_at >= after)

    # newest first so the limit keeps the latest, then flip to oldest-first
    recent = query.order_by(Message.created_at.desc()).limit(MAX_POLL_MESSAGES).all()
    messages = [
        {
            "id": str(m.id),
            "sender": m.sender,
            "text": m.text,
            "created_at": m.created_at.isoformat(),
        }
        for m in reversed(recent)
    ]

    if messages:
        latest_at = messages[-1]["created_at"]
    else:
        latest_at = str(after_raw) if after_raw else None

    # never includes public_token, lead details, or organization ids
    return jsonify({
        "messages": messages,
        "latest_at": latest_at,
        "ai_paused": not conversation.ai_enabled,
    })


# ---------- agent-facing: login required, scoped to the agent's own org ----------

@conversations_bp.route('/<conversation_id>/take-over', methods=['POST'])
@jwt_required()
def take_over(conversation_id):
    if not is_valid_uuid(conversation_id):
        return jsonify({"error": "conversation not found"}), 404

    org_id = get_jwt()["organization_id"]
    conversation = Conversation.query.filter_by(
        id=conversation_id, organization_id=org_id
    ).first()
    if not conversation:
        return jsonify({"error": "conversation not found"}), 404

    conversation.ai_enabled = False
    db.session.commit()

    return jsonify({
        "conversation_id": conversation.id,
        "ai_enabled": False
    })


@conversations_bp.route('/<conversation_id>/resume', methods=['POST'])
@jwt_required()
def resume_ai(conversation_id):
    if not is_valid_uuid(conversation_id):
        return jsonify({"error": "conversation not found"}), 404

    org_id = get_jwt()["organization_id"]
    conversation = Conversation.query.filter_by(
        id=conversation_id, organization_id=org_id
    ).first()
    if not conversation:
        return jsonify({"error": "conversation not found"}), 404

    conversation.ai_enabled = True
    db.session.commit()

    return jsonify({
        "conversation_id": conversation.id,
        "ai_enabled": True
    })