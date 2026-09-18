from flask import Blueprint, request, jsonify
from app.extensions import db
from app.modules.conversations.models import Conversation, Message
from app.modules.organizations.models import Organization
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

    ai_reply_text = generate_ai_response(user_text)

    ai_message = Message(
        organization_id=demo_org.id,
        conversation_id=conversation.id,
        sender="ai",
        text=ai_reply_text
    )
    db.session.add(ai_message)
    db.session.commit()

    return jsonify({"reply": ai_reply_text})