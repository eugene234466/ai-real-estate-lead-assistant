from extensions import db
from sqlalchemy.dialects.postgresql import UUID
from backend.app.shared.db_base import TenantModel

class Conversation(TenantModel):
    __tablename__ = 'conversations'

    ai_enabled = db.Column(db.Boolean, default=True)
    status = db.Column(db.Enum('active', 'inactive', name='conversation_status'), default='active')
    messages = db.relationship('Message', backref='conversation', lazy=True)



class Message(TenantModel):
    __tablename__ = 'messages'

    conversation_id = db.Column(UUID(as_uuid=True), db.ForeignKey('conversations.id'), nullable=False)
    sender = db.Column(db.Enum('user', 'ai', 'agent', name='message_sender'), nullable=False)
    text = db.Column(db.Text, nullable=False)