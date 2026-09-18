from logging.config import fileConfig
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

load_dotenv()

# make sure the app package is importable
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.extensions import db
from app.modules.organizations.models import Organization
from app.modules.conversations.models import Conversation, Message

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option(
    "sqlalchemy.url", os.getenv("SQLALCHEMY_DATABASE_URI")
)

target_metadata = db.metadata