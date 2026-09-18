from extensions import db
from backend.app.shared.db_base import TenantModel, BaseModel

class Conversation(TenantModel):
    __tablename__ = 'conversation'
    lead_id = db.Column(db.uuid, db.ForeignKey('lead.id'), nullable=True)
    ai_enabled = db.Column(db.Boolean, default=True)
    status = db.Column(db.enum('active', 'inactive', name='conversation_status'), default='active')
    messages = db.relationship('Message', backref='conversation', lazy=True)
    
    
class Message(TenantModel):
    __tablename__ = 'messages'
    conversation_id = db.Column(db.uuid, db.ForeignKey('conversation.id'), nullable=False)
    sender = db.Column(db.enum('user', 'ai', 'agent', name='message_sender'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(BaseModel.created_at.type, default=BaseModel.created_at.default)