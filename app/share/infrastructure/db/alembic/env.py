import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
import sqlalchemy as sa
from sqlmodel import SQLModel


from app.config import settings

# Registrar todos los modelos SQLModel para que Alembic los detecte
from app.modules.legal_library.infrastructure.models import LegalArticle  # noqa: F401

config = context.config
fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


import builtins
import sqlmodel
import pgvector.sqlalchemy

# Inyectar en builtins para que las migraciones los vean globalmente sin import
builtins.sqlmodel = sqlmodel
builtins.pgvector = pgvector
# Inyectar tipos específicos de SQLModel que Alembic suele usar sin prefijo
for name in dir(sqlmodel.sql.sqltypes):
    if not name.startswith("_"):
        setattr(builtins, name, getattr(sqlmodel.sql.sqltypes, name))


def run_migrations_offline():
    context.configure(
        url=settings.db_url_async,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        user_module_prefix=None,
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        user_module_prefix=None,
    )


    with context.begin_transaction():
        # Asegurar que la extensión vectorial existe antes de cualquier tabla
        connection.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
        
        context.run_migrations()






async def run_migrations_online():
    connectable = create_async_engine(settings.db_url_async)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
