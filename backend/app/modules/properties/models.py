from app.extensions import db
from app.shared.db_base import TenantModel


class Property(TenantModel):
    __tablename__ = 'properties'

    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    property_type = db.Column(db.String(100), nullable=False)
    listing_type = db.Column(db.Enum('sale', 'rent', name='listing_type'), nullable=False)
    price = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(10), default='USD')
    location = db.Column(db.String(255), nullable=False)
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Integer)
    amenities = db.Column(db.JSON)
    availability_status = db.Column(
        db.Enum('available', 'unavailable', 'pending', name='availability_status'),
        nullable=False,
        default='available'
    )