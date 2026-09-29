# backend/app/modules/followups/tasks.py

from datetime import datetime, timedelta, timezone
import logging

from app.celery_app import celery
from app import create_app
from app.extensions import db
from app.modules.followups.models import FollowUp
from app.modules.leads.models import Lead
from app.modules.leads.state_machine import apply_lead_stage
from app.modules.conversations.models import Conversation, Message
from app.modules.ai_engine.service import generate_ai_response

logger = logging.getLogger(__name__)

INACTIVITY_THRESHOLD = timedelta(minutes=2)  # short for testing; raise for production
ACTIVE_STAGES = {"ENGAGED", "QUALIFYING", "QUALIFIED", "BOOKING"}


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
        followup.sent_at = datetime.now(timezone.utc).replace(tzinfo=None)
        followup.message_text = ai_result["response"]
        db.session.commit()

        logger.info("Follow-up sent for lead %s", lead.id)


@celery.task
def scan_inactive_leads():
    app = create_app()
    with app.app_context():
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        cutoff = now - INACTIVITY_THRESHOLD

        leads = Lead.query.filter(
            Lead.lead_stage.in_(ACTIVE_STAGES),
            Lead.last_contact_at < cutoff
        ).all()

        for lead in leads:
            conversation = Conversation.query.filter_by(lead_id=lead.id).first()
            if not conversation or not conversation.ai_enabled:
                continue  # never follow up while a human is in charge

            last_followup = (
                FollowUp.query
                .filter_by(lead_id=lead.id)
                .order_by(FollowUp.created_at.desc())
                .first()
            )

            if last_followup and last_followup.status == "SCHEDULED":
                continue  # one already queued, don't duplicate

            if last_followup and last_followup.status == "SENT" \
                    and last_followup.sent_at and last_followup.sent_at > lead.last_contact_at:
                # already followed up since the lead last spoke — did they respond?
                if now - last_followup.sent_at > INACTIVITY_THRESHOLD:
                    apply_lead_stage(lead, "NURTURE")
                    db.session.commit()
                continue

            followup = FollowUp(
                organization_id=lead.organization_id,
                lead_id=lead.id,
                conversation_id=conversation.id,
                scheduled_at=now,
                status="SCHEDULED"
            )
            db.session.add(followup)
            db.session.commit()

            send_followup.delay(str(followup.id))
            logger.info("Scheduled follow-up %s for lead %s", followup.id, lead.id)