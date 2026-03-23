#!/bin/sh
set -e

# Variable para la ruta de versiones dentro del contenedor
VERSIONS_DIR="app/share/infrastructure/db/alembic/versions"

echo "⏳ Esperando a que PostgreSQL esté listo..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" 2>/dev/null; do
  sleep 1
done

# Crear carpeta de versiones si no existe por algún motivo
if [ ! -d "$VERSIONS_DIR" ]; then
  echo "📂 Creando directorio de versiones de Alembic en $VERSIONS_DIR..."
  mkdir -p "$VERSIONS_DIR"
fi

# Si la carpeta está vacía, generar la migración inicial automáticamente.
# NOTA: En producción esto es arriesgado si no hay una base de datos real sincronizada, 
# pero para desarrollo y MVP es muy útil.
if [ -z "$(ls -A "$VERSIONS_DIR" 2>/dev/null)" ]; then
  echo "✨ El directorio de versiones está vacío. Generando migración inicial..."
  uv run alembic revision --autogenerate -m "initial_migration"
fi

echo "⏳ Aplicando migraciones pendientes..."
uv run alembic upgrade head
echo "✅ Migraciones aplicadas."

echo "🚀 Iniciando servidor Uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 $FASTAPI_MODE
