from app.extensions import db
from app.shared.db_base import TenantModel
from sqlalchemy.dialects.postgresql import UUID

class Lead(TenantModel):
    __tablename__ = 'leads'
    name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    phone = db.Column(db.String(13))
    source = db.Column(db.String(50))
    property_id = db.Column(UUID(as_uuid=True), db.ForeignKey('properties.id'))
    intent = db.Column(db.String(500))
    buy_or_rent = db.Column(db.Enum('buy', 'rent', name='intent_type'))
    budget = db.Column(db.Numeric(13,2))
    location_preference = db.Column(db.String(500))
    timeline = db.Column(db.String(200))
    lead_stage = db.Column(
        db.Enum('NEW', 'ENGAGED', 'QUALIFYING', 'QUALIFIED',
                'BOOKING', 'BOOKED', 'NURTURE',
                'HUMAN_HANDOFF', 'CLOSED',
            name='lead_stage',            
        ),
        nullable=False,
        default='NEW'
    )
    assigned_agent_id = db.Column(UUID(as_uuid=True))
    last_contact_at = db.Column(db.DateTime)
    next_follow_up_at = db.Column(db.DateTime)
    
     