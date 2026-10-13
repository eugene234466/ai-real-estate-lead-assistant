# backend/app/modules/inbox/routes.py

from datetime import datetime, timezone
import logging
import uuid

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy import func

from app.extensions import db
from app.modules.conversations.models import Conversation, Message
from app.modules.leads.models import Lead
from app.modules.notifications.models import Notification

logger = logging.getLogger(__name__)

inbox_bp = Blueprint('inbox', __name__)

MAX_AGENT_MESSAGE_LENGTH = 1000
MAX_DETAIL_MESSAGES = 200
PREVIEW_LENGTH = 100


# ---------- helpers ----------

def is_valid_uuid(value):
    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False


def parse_int(value, default, minimum, maximum):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, number))


def iso(value):
    return value.isoformat() if value else None


def get_org_conversation(conversation_id, org_id):
    # same result for "doesn't exist" and "belongs to another org"
    if not is_valid_uuid(conversation_id):
        return None
    return Conversation.query.filter_by(
        id=conversation_id, organization_id=org_id
    ).first()


def lead_summary(lead):
    if lead is None:
        return None
    return {
        "id": str(lead.id),
        "name": lead.name,
        "lead_stage": lead.lead_stage,
        "buy_or_rent": lead.buy_or_rent,
        "budget": float(lead.budget) if lead.budget is not None else None,
        "location_preference": lead.location_preference,
    }


def lead_detail(lead):
    if lead is None:
        return None
    data = lead_summary(lead)
    data.update({
        "email": lead.email,
        "phone": lead.phone,
        "source": lead.source,
        "intent": lead.intent,
        "timeline": lead.timeline,
        "property_id": str(lead.property_id) if lead.property_id else None,
        "assigned_agent_id": str(lead.assigned_agent_id) if lead.assigned_agent_id else None,
        "last_contact_at": iso(lead.last_contact_at),
        "next_follow_up_at": iso(lead.next_follow_up_at),
    })
    return data


def message_json(message):
    return {
        "id": str(message.id),
        "sender": message.sender,
        "text": message.text,
        "created_at": iso(message.created_at),
    }


def notification_json(notification):
    return {
        "id": str(notification.id),
        "type": notification.type,
        "message": notification.message,
        "is_read": notification.is_read,
        "lead_id": str(notification.lead_id) if notification.lead_id else None,
        "conversation_id": str(notification.conversation_id) if notification.conversation_id else None,
        "appointment_id": str(notification.appointment_id) if notification.appointment_id else None,
        "created_at": iso(notification.created_at),
    }


# ---------- conversations ----------

@inbox_bp.route('/conversations', methods=['GET'])
@jwt_required()
def list_conversations():
    org_id = get_jwt()["organization_id"]
    limit = parse_int(request.args.get('limit'), 20, 1, 50)
    page = parse_int(request.args.get('page'), 1, 1, 10000)

    # newest activity first. Conversation.updated_at won't do: it doesn't change when messages arrive
    last_msg = (
        db.session.query(
            Message.conversation_id.label("cid"),
            func.max(Message.created_at).label("last_at")
        )
        .filter(Message.organization_id == org_id)
        .group_by(Message.conversation_id)
        .subquery()
    )

    rows = (
        db.session.query(Conversation, last_msg.c.last_at)
        .outerjoin(last_msg, Conversation.id == last_msg.c.cid)
        .filter(Conversation.organization_id == org_id)
        .order_by(last_msg.c.last_at.desc().nulls_last())
        .limit(limit)
        .offset((page - 1) * limit)
        .all()
    )

    conversations = [c for c, _ in rows]
    lead_ids = [c.lead_id for c in conversations if c.lead_id]
    conversation_ids = [c.id for c in conversations]

    leads = {}
    if lead_ids:
        leads = {
            lead.id: lead
            for lead in Lead.query.filter(
                Lead.id.in_(lead_ids), Lead.organization_id == org_id
            ).all()
        }

    unread = {}
    if conversation_ids:
        unread = dict(
            db.session.query(Notification.conversation_id, func.count(Notification.id))
            .filter(
                Notification.organization_id == org_id,
                Notification.is_read.is_(False),
                Notification.conversation_id.in_(conversation_ids)
            )
            .group_by(Notification.conversation_id)
            .all()
        )

    result = []
    for conversation, last_at in rows:
        last_message = (
            Message.query
            .filter_by(conversation_id=conversation.id, organization_id=org_id)
            .order_by(Message.created_at.desc())
            .first()
        )
        result.append({
            "id": str(conversation.id),
            "ai_enabled": conversation.ai_enabled,
            "status": conversation.status,
            "created_at": iso(conversation.created_at),
            "last_message": last_message.text[:PREVIEW_LENGTH] if last_message else None,
            "last_message_sender": last_message.sender if last_message else None,
            "last_message_at": iso(last_at),
            "unread_notifications": unread.get(conversation.id, 0),
            "lead": lead_summary(leads.get(conversation.lead_id)),
        })

    # public_token is never included: it's the visitor's session secret
    return jsonify({"conversations": result, "page": page, "limit": limit})


@inbox_bp.route('/conversations/<conversation_id>', methods=['GET'])
@jwt_required()
def get_conversation(conversation_id):
    org_id = get_jwt()["organization_id"]
    conversation = get_org_conversation(conversation_id, org_id)
    if not conversation:
        return jsonify({"error": "conversation not found"}), 404

    lead = None
    if conversation.lead_id:
        lead = Lead.query.filter_by(
            id=conversation.lead_id, organization_id=org_id
        ).first()

    # keep the latest messages: query newest-first, then flip to oldest-first
    recent = (
        Message.query
        .filter_by(conversation_id=conversation.id, organization_id=org_id)
        .order_by(Message.created_at.desc())
        .limit(MAX_DETAIL_MESSAGES)
        .all()
    )

    return jsonify({
        "conversation": {
            "id": str(conversation.id),
            "ai_enabled": conversation.ai_enabled,
            "status": conversation.status,
            "created_at": iso(conversation.created_at),
        },
        "lead": lead_detail(lead),
        "messages": [message_json(m) for m in reversed(recent)],
    })


@inbox_bp.route('/conversations/<conversation_id>/messages', methods=['POST'])
@jwt_required()
def send_agent_message(conversation_id):
    org_id = get_jwt()["organization_id"]
    conversation = get_org_conversation(conversation_id, org_id)
    if not conversation:
        return jsonify({"error": "conversation not found"}), 404

    body = request.get_json(silent=True) or {}
    text = body.get('text')

    if not isinstance(text, str) or not text.strip():
        return jsonify({"error": "text is required"}), 400
    if len(text) > MAX_AGENT_MESSAGE_LENGTH:
        return jsonify({"error": "message too long"}), 400

    message = Message(
        organization_id=org_id,
        conversation_id=conversation.id,
        sender="agent",
        text=text.strip()
    )
    db.session.add(message)

    # an agent speaking means the AI steps back, so the visitor never hears two voices
    conversation.ai_enabled = False

    if conversation.lead_id:
        lead = Lead.query.filter_by(
            id=conversation.lead_id, organization_id=org_id
        ).first()
        if lead:
            lead.last_contact_at = datetime.now(timezone.utc).replace(tzinfo=None)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception("Failed to save agent message for conversation %s", conversation.id)
        return jsonify({"error": "Could not send the message"}), 500

    return jsonify(message_json(message)), 201


# ---------- notifications ----------

@inbox_bp.route('/notifications', methods=['GET'])
@jwt_required()
def list_notifications():
    org_id = get_jwt()["organization_id"]
    limit = parse_int(request.args.get('limit'), 50, 1, 100)

    notifications = (
        Notification.query
        .filter_by(organization_id=org_id)
        .order_by(Notification.is_read.asc(), Notification.created_at.desc())
        .limit(limit)
        .all()
    )

    return jsonify({"notifications": [notification_json(n) for n in notifications]})


@inbox_bp.route('/notifications/<notification_id>/read', methods=['POST'])
@jwt_required()
def mark_notification_read(notification_id):
    org_id = get_jwt()["organization_id"]
    if not is_valid_uuid(notification_id):
        return jsonify({"error": "notification not found"}), 404

    notification = Notification.query.filter_by(
        id=notification_id, organization_id=org_id
    ).first()
    if not notification:
        return jsonify({"error": "notification not found"}), 404

    notification.is_read = True
    db.session.commit()

    return jsonify(notification_json(notification))