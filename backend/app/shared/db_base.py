from extensions import db

class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.uuid, primary_key=True, default=db.generate_uuid)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    

class Message(TenantModel):
    __tablename__ = 'messages'

    conversation_id = db.Column(UUID(as_uuid=True), db.ForeignKey('conversations.id'), nullable=False)
    sender = db.Column(db.Enum('user', 'ai', 'agent', name='message_sender'), nullable=False)
    text = db.Column(db.Text, nullable=False)