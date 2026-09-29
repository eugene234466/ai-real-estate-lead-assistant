from app.extensions import db
from app.shared.db_base import TenantModel
from sqlalchemy.dialects.postgresql import UUID


class Notification(TenantModel):
    __tablename__ = "notifications"

    lead_id = db.Column(UUID(as_uuid=True), db.ForeignKey('leads.id'))
    conversation_id = db.Column(UUID(as_uuid=True), db.ForeignKey('conversations.id'))
    appointment_id = db.Column(UUID(as_uuid=True), db.ForeignKey('appointments.id'))
    type = db.Column(
        db.Enum("HUMAN_HANDOFF", "NEW_APPOINTMENT", "NEW_LEAD", name='notification_type'),
        nullable=False
    )
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False)