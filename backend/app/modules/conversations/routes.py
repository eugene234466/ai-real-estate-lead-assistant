# backend/app/modules/conversations/routes.py

from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.modules.conversations.models import Conversation, Message
from app.modules.organizations.models import Organization
from app.modules.leads.models import Lead
from app.modules.leads.state_machine import apply_lead_stage
from app.modules.ai_engine.service import generate_ai_response

conversations_bp = Blueprint('conversations', __name__)


@conversations_bp.route('/message', methods=['POST'])
def send_message():
    body = request.get_json()
    user_text = body.get('text') if body else None

    if not user_text:
        return jsonify({"error": "text is required"}), 400

    demo_org = Organization.query.filter_by(name="Example Realty").first()
    if not demo_org:
        return jsonify({"error": "demo organization not seeded"}), 500

    conversation = Conversation.query.filter_by(organization_id=demo_org.id).first()
    if not conversation:
        conversation = Conversation(organization_id=demo_org.id)
        db.session.add(conversation)
        db.session.commit()

    user_message = Message(
        organization_id=demo_org.id,
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
            "message": "This conversation is currently being handled by an agent."
        })

    ai_result = generate_ai_response(user_text, demo_org.id)

    if conversation.lead_id is None:
        lead = Lead(organization_id=demo_org.id)
        db.session.add(lead)
        db.session.commit()
        conversation.lead_id = lead.id
        db.session.commit()
    else:
        lead = Lead.query.filter_by(id=conversation.lead_id).first()

    if ai_result['property_id'] is not None:
        lead.property_id = ai_result['property_id']

    if ai_result['buy_or_rent'] is not None:
        lead.buy_or_rent = ai_result['buy_or_rent']

    if ai_result['budget'] is not None:
        lead.budget = ai_result['budget']

    if ai_result['timeline'] is not None:
        lead.timeline = ai_result['timeline']

    if ai_result['intent'] is not None:
        lead.intent = ai_result['intent']

    transition_applied = apply_lead_stage(lead, ai_result["lead_stage"])
    if not transition_applied:
        ai_result["human_handoff_required"] = True

    lead.last_contact_at = datetime.now(timezone.utc)
    db.session.commit()

    if ai_result["human_handoff_required"]:
        conversation.ai_enabled = False
        db.session.commit()

    ai_message = Message(
        organization_id=demo_org.id,
        conversation_id=conversation.id,
        sender="ai",
        text=ai_result["response"]
    )
    db.session.add(ai_message)
    db.session.commit()

    return jsonify({"reply": ai_result["response"]})