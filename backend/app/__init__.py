from flask import Flask
from .extensions import db, migrate


def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    db.init_app(app)
    migrate.init_app(app, db)

    # import models so Alembic can detect them via db.metadata
    from .modules.organizations.models import Organization
    from .modules.conversations.models import Conversation, Message

    return app