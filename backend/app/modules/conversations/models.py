# backend/app/modules/conversations/models.py

from app.extensions import db
from sqlalchemy.dialects.postgresql import UUID
from app.shared.db_base import TenantModel
import secrets

class Conversation(TenantModel):
    __tablename__ = 'conversations'

    ai_enabled = db.Column(db.Boolean, default=True)
    status = db.Column(db.Enum('active', 'inactive', name='conversation_status'), default='active')
    messages = db.relationship('Message', backref='conversation', lazy=True)
    lead_id = db.Column(UUID(as_uuid=True), db.ForeignKey('leads.id'))
    public_id = db.Column(db.String(64), nullable=False, unique=True, index=True, default=lambda: secrets.token_urlsafe(32))

class Message(TenantModel):
    __tablename__ = 'messages'

    conversation_id = db.Column(UUID(as_uuid=True), db.ForeignKey('conversations.id'), nullable=False)
    sender = db.Column(db.Enum('user', 'ai', 'agent', name='message_sender'), nullable=False)
    text = db.Column(db.Text, nullable=False)
   
    