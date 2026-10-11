from app.extensions import db
from app.shared.db_base import BaseModel
import secrets


class Organization(BaseModel):
    __tablename__ = 'organizations'

    name = db.Column(db.String, nullable=False)
    widget_key =db.Column(db.String(64), nullable=False, unique=True, index=True, default=lambda: secrets.token_urlsafe(24))
    