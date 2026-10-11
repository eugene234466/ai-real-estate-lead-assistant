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
from app.modules.leads.state_machine import apply_lead_stage
from app.modules.ai_engine.service import generate_ai_response
from app.modules.notifications.models import Notification

logger = logging.getLogger(__name__)

conversations_bp = Blueprint('conversations', __name__)

MAX_MESSAGE_LENGTH = 1000
FALLBACK_REPLY = "Sorry, I'm having trouble right now. An agent will follow up with you shortly."


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

    db.session.add(Message(
        organization_id=org.id,
        conversation_id=conversation.id,
        sender="user",
        text=user_text
    ))
    db.session.commit()

    if not conversation.ai_enabled:
        return jsonify({
            "reply": None,
            "ai_paused": True,
            "message": "This conversation is currently being handled by an agent.",
            "conversation_token": conversation.public_token
        })

    try:
        ai_result = generate_ai_response(user_text, org.id)
    except Exception:
        logger.exception("AI generation failed for conversation %s", conversation.id)
        return jsonify({"error": "The assistant is unavailable right now. Please try again."}), 503

    if conversation.lead_id is None:
        lead = Lead(organization_id=org.id, source="web_chat")
        db.session.add(lead)
        db.session.flush()
        conversation.lead_id = lead.id
    else:
        lead = Lead.query.filter_by(
            id=conversation.lead_id, organization_id=org.id
        ).first()

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

    budget = clean_budget(ai_result.get('budget'))
    if budget is not None:
        lead.budget = budget

    if ai_result.get('timeline') is not None:
        lead.timeline = clean_text(ai_result['timeline'], 200)

    if ai_result.get('intent') is not None:
        lead.intent = clean_text(ai_result['intent'], 500)

    handoff_required = bool(ai_result.get("human_handoff_required"))
    if not apply_lead_stage(lead, ai_result["lead_stage"]):
        handoff_required = True

    lead.last_contact_at = datetime.now(timezone.utc).replace(tzinfo=None)

    reply_text = ai_result.get("response")
    if not isinstance(reply_text, str) or not reply_text.strip():
        reply_text = FALLBACK_REPLY
        handoff_required = True

    if handoff_required:
        conversation.ai_enabled = False
        db.session.add(Notification(
            organization_id=org.id,
            lead_id=lead.id,
            conversation_id=conversation.id,
            type="HUMAN_HANDOFF",
            message=f"Conversation needs human attention - lead stage: {lead.lead_stage}"
        ))

    db.session.add(Message(
        organization_id=org.id,
        conversation_id=conversation.id,
        sender="ai",
        text=reply_text
    ))

    try:
        db.session.commit()  # lead update, handoff, notification, and reply land together
    except Exception:
        db.session.rollback()
        logger.exception("Failed to save AI reply for conversation %s", conversation.id)
        return jsonify({"error": "Could not save the reply. Please try again."}), 500

    return jsonify({
        "reply": reply_text,
        "conversation_token": conversation.public_token
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