from extensions import db

class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.uuid, primary_key=True, default=db.generate_uuid)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    

class TenantModel(BaseModel):
    __abstract__ = True
    organization_id = db.Column(db.uuid, db.ForeignKey('organization.id'), nullable=False)
    
    
