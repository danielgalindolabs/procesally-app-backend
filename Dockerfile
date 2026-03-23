# === ETAPA 0: PREPARACIÓN NATIVA CON UV ===
FROM python:3.12-slim-bookworm AS builder

# Instala el binario oficial de UV de Astral directamente
COPY --from=ghcr.io/astral-sh/uv:0.4.15 /uv /uvx /bin/

# Configuraciones para evitar demoras y optimizar peso
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Instalación por capas (Agresiva optimización de caché en Docker)
# Si no modificaste nuevas librerías, docker ignorará este paso y cargará de memoria.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# === ETAPA 1: COMPILACIÓN DEL CÓDIGO FUENTE ===
COPY . .
RUN uv sync --frozen --no-dev


# === ETAPA 2: EJECUCIÓN DEL SERVIDOR EN PRODUCCIÓN ===
FROM python:3.12-slim-bookworm

# Copiamos el binario de uv para poder usar 'uv run' en el entrypoint
COPY --from=builder /bin/uv /bin/uvx /bin/

ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client && rm -rf /var/lib/apt/lists/*

# Copiamos la app ya compilada (con su .venv optimizado) desde el paso anterior
COPY --from=builder /app /app/

# Ponemos al venv en el PATH para que uvicorn y python corran por defecto
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
