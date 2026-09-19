from app.extensions import db
from app.shared.db_base import TenantModel
from sqlalchemy.dialects.postgresql import UUID

class Lead(TenantModel):
    __tablename__ = 'leads'
    name = db.Column(db.String(50))
    email = db.Column(db.String(30))
    phone = db.Column(db.String(13))
    source = db.Column(db.String(50))
    property_id = db.Column(UUID(as_uuid=True), db.ForeignKey('properties.id'))
    intent = db.Column(db.String(500))
    buy_or_rent = db.Column(db.Enum('buy', 'rent', name='intent_type'))
    budget = db.Column(db.Numeric(13,2))