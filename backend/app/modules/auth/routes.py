from flask import Blueprint, request, jsonify
from app.extensions import db
from app.extensions import bcrypt
from app.modules.auth.models import User
from app.modules.organizations.models import Organization 
from flask_jwt_extended import create_access_token, create_refresh_token, set_access_cookies, set_refresh_cookies

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    body = request.get_json()
    org_name = body.get('organization_name')
    email = body.get('email')
    password = body.get('password')
    full_name = body.get('full_name')
    
    if org_name is None or email is None or password is None:
        return jsonify({'error':'organization_name, email, and password are required fields'}), 400
    
    existing = User.query.filter_by(email=email).first()
    
    if existing:
        return jsonify({'error':'An account with that email already exists'}), 409
    
    try:
        organization = Organization(name=org_name)
        db.session.add(organization)
        db.session.flush()
        
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
        user = User(
            organization_id=organization.id,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role='OWNER'
        )
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Signup failed'}), 500
    
    access_token = create_access_token(identity=str(user.id), additional_claims={
        "organization_id": str(user.organization_id),
        "role": user.role
    })
    refresh_token = create_refresh_token(identity=str(user.id))
    
    response = jsonify({
        'user_id': user.id,
        'organization_id': organization.id,
        'email': user.email,
        'role': user.role
    })
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)
    return response, 201


@auth_bp.route('/login', methods=['POST'])
def login():
    body = request.get_json()
    email = body.get('email')
    password = body.get('password')
    
    if email is None or password is None:
        return jsonify({'error':'email and password are required'}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if user is None or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({'error':'Invalid email or password'}), 401
    
    if not user.is_active:
        return jsonify({'error':'This account has been deactivated'}), 403
    
    access_token = create_access_token(identity=str(user.id), additional_claims={
        "organization_id": str(user.organization_id),
        "role": user.role
    })
    refresh_token = create_refresh_token(identity=str(user.id))
    
    response = jsonify({
        'user_id': user.id,
        'organization_id': user.organization_id,
        'email': user.email,
        'role': user.role 
    })
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)
    
    return response, 200
    