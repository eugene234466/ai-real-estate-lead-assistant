# backend/app/shared/db_base.py

import uuid
from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db


class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())


class TenantModel(BaseModel):
    __abstract__ = True

    organization_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('organizations.id'),
        nullable=False,
        index=True
    )