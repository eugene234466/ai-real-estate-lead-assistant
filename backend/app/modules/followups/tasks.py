# backend/app/modules/followups/tasks.py

from datetime import datetime, timezone
import logging

from app.celery_app import celery
from app import create_app
from app.extensions import db
from app.modules.followups.models import FollowUp
from app.modules.leads.models import Lead
from app.modules.conversations.models import Conversation, Message
from app.modules.ai_engine.service import generate_ai_response

logger = logging.getLogger(__name__)


@celery.task
def send_followup(followup_id):
    app = create_app()
    with app.app_context():
        followup = FollowUp.query.filter_by(id=followup_id).first()
        if not followup or followup.status != "SCHEDULED":
            logger.warning("Follow-up not found or already processed: %s", followup_id)
            return

        lead = Lead.query.filter_by(id=followup.lead_id).first()
        conversation = Conversation.query.filter_by(id=followup.conversation_id).first()

        if not lead or not conversation:
            logger.warning("Follow-up %s missing lead or conversation", followup_id)
            followup.status = "FAILED"
            db.session.commit()
            return

        followup_prompt_text = (
            "It's been a while since the lead last responded. "
            "Write a brief, friendly follow-up message checking if "
            "they're still interested."
        )

        ai_result = generate_ai_response(followup_prompt_text, lead.organization_id)

        message = Message(
            organization_id=lead.organization_id,
            conversation_id=conversation.id,
            sender="ai",
            text=ai_result["response"]
        )
        db.session.add(message)

        followup.status = "SENT"
        followup.sent_at = datetime.now(timezone.utc)
        followup.message_text = ai_result["response"]
        db.session.commit()

        logger.info("Follow-up sent for lead %s", lead.id)