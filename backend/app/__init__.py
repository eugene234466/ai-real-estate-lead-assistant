from flask import Flask
from .extensions import db, migrate


def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    db.init_app(app)
    migrate.init_app(app, db)

    from .modules.organizations.models import Organization
    from .modules.conversations.models import Conversation, Message

    from .modules.conversations.routes import conversations_bp
    app.register_blueprint(conversations_bp, url_prefix='/api/chat')

    return app