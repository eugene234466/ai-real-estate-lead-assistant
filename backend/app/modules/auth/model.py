from app.extensions import db
from app.shared.db_base import TenantModel
from sqlalchemy.dialects.postgresql import UUID

class User(TenantModel):
    __tablename__ = "users"
    
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255))
    role = db.Column(
        db.Enum("OWNER", "ADMIN", "AGENT", name="user_role"),
        nullable=False,
        default="AGENT"
    )
    is_active = db.Column(db.Boolean, nullable=False, default=True)