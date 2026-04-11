"""Alembic env.py for visit_management_svc — schema: visit_schema

All migrations run inside the 'visit_schema' Postgres schema so multiple
services share the same 'in_home_care_platform' database without colliding.
"""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, text

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

SCHEMA = "visit_schema"


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=None,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=SCHEMA,
        include_schemas=True,
    )
    with context.begin_transaction():
        context.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
        context.execute(f"SET search_path TO {SCHEMA}")
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(config.get_main_option("sqlalchemy.url"))
    with connectable.connect() as connection:
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"))
        connection.execute(text(f"SET search_path TO {SCHEMA}"))
        connection.commit()

        context.configure(
            connection=connection,
            target_metadata=None,
            version_table_schema=SCHEMA,
            include_schemas=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
