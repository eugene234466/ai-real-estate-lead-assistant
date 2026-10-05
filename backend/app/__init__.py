from flask import Flask
from flask_cors import CORS
from .extensions import db, migrate
from .extensions import jwt, bcrypt


def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)

    from .modules.organizations.models import Organization
    from .modules.conversations.models import Conversation, Message
    from .modules.properties.models import Property
    from .modules.leads.models import Lead
    from .modules.appointments.models import Appointment
    from .modules.followups.models import FollowUp
    from .modules.notifications.models import Notification
    from .modules.auth.models import User
    

    from .modules.conversations.routes import conversations_bp
    app.register_blueprint(conversations_bp, url_prefix='/api/chat')

    from .modules.appointments.routes import appointments_bp
    app.register_blueprint(appointments_bp, url_prefix='/api/appointments')
    
    from .modules.auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    return app