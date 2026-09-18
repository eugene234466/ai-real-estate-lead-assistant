from extensions import db
from backend.app.shared.db_base import BaseModel


class Organization(BaseModel):
    __tablename__ = 'organizations'

    name = db.Column(db.String, nullable=False)