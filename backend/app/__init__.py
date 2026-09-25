from flask import Flask
from .extensions import db, migrate


def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    db.init_app(app)
    migrate.init_app(app, db)

    from .modules.organizations.models import Organization
    from .modules.conversations.models import Conversation, Message
    from .modules.properties.models import Property
    from .modules.leads.models import Lead
    from .modules.appointments.models import Appointment
    

    from .modules.conversations.routes import conversations_bp
    app.register_blueprint(conversations_bp, url_prefix='/api/chat')
    from .modules.appointments.routes import appointments_bp
    app.register_blueprint(appointments_bp, url_prefix='/api/appointments')
    

    return app