from app.extensions import db
from app.shared.db_base import TenantModel
from sqlalchemy.dialects.postgresql import UUID

class Appointment(TenantModel):
    __tablename__ = 'appointments'
    
    lead_id = db.Column(UUID(as_uuid=True), db.ForeignKey('leads.id'), nullable=False)
    property_id = db.Column(UUID(as_uuid=True), db.ForeignKey('properties.id'))
    scheduled_at = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=30)
    status = db.Column(
        db.Enum('PENDING', 'CONFIRMED', 'CANCELLED',
            'COMPLETED', 'NO_SHOW', name='appointment_status'
        ),
        nullable=False,
        default='PENDING'
    )
    notes = db.Column(db.Text)
    
    