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
from app.modules.properties.models import Property
from app.modules.leads.models import Lead
from app.modules.appointments.models import Appointment

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

database_url = os.getenv("SQLALCHEMY_DATABASE_URI")
if database_url is None:
    raise RuntimeError("SQLALCHEMY_DATABASE_URI is not set in the environment")

print("USING DB URL:", database_url[:40], "...")

config.set_main_option("sqlalchemy.url", database_url)

target_metadata = db.metadata
print("REGISTERED TABLES:", list(target_metadata.tables.keys()))


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()