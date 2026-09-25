from app.extensions import db
from app.shared.db_base import TenantModel
from sqlalchemy.dialects.postgresql import UUID


class FollowUp(TenantModel):
    __tablename__ = "follow_ups"

    lead_id = db.Column(UUID(as_uuid=True), db.ForeignKey('leads.id'), nullable=False)
    conversation_id = db.Column(UUID(as_uuid=True), db.ForeignKey('conversations.id'))
    scheduled_at = db.Column(db.DateTime, nullable=False)
    sent_at = db.Column(db.DateTime)
    status = db.Column(
        db.Enum('SCHEDULED', 'SENT', 'CANCELLED', 'FAILED', name='followup_status'),
        nullable=False,
        default='SCHEDULED'
    )
    message_text = db.Column(db.Text)