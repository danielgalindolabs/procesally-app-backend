# AGENTS.md - Procesally Backend

Guía para agentes de código (OpenCode, Cursor, Copilot) en este repositorio.

## Stack
- FastAPI (Python 3.12+)
- PostgreSQL + pgvector
- Arquitectura: Hexagonal + DDD
- Package manager: UV

---

## Build / Lint / Test

### Comandos principales
```bash
make lint
make test
```

### Manual (UV)
```bash
# Lint
uv run isort app
uv run black app
uv run ruff check app
uv run flake8 app

# Tests
uv run pytest

# Test individual
uv run pytest tests/path/to/file.py::test_name -v

# Por patrón
uv run pytest -k "search" -v

# Coverage
uv run pytest --cov=app tests/

# Autofix
uv run ruff check app --fix
```

### Dev server
```bash
uv run fastapi run app/main.py --host 0.0.0.0 --port 8000
```

---

## Code Style

### Naming
- snake_case → funciones, variables, archivos
- PascalCase → clases
- SCREAMING_SNAKE_CASE → env vars

### Formatting
- Black + isort obligatorios
- Mantener imports ordenados
- Evitar lógica innecesariamente compleja

### Imports
```python
# stdlib
import logging
from typing import List, Optional

# third-party
from fastapi import APIRouter

# local
from app.modules.legal_library.adapters.app_domain_mapper import AppDomainMapper
```

Reglas:
- Usar imports absolutos
- Separar grupos con línea en blanco

### Types
- Tipado obligatorio
- Usar Optional[X], List[X]
- Evitar Any

---

## Arquitectura

Estructura:
```
domain → entidades puras
application → casos de uso
infrastructure → DB / servicios externos
presentation → API
```

### Domain
- Sin dependencias externas
- Solo lógica de negocio

### Application
- Orquesta casos de uso
- Usa interfaces (no implementaciones)

### Infrastructure
- Implementa repositorios
- Maneja DB, embeddings, servicios externos

### Presentation
- FastAPI routers
- Schemas Pydantic

---

## Error Handling

- Usar excepciones custom
- No filtrar errores de infra directamente
- Loggear con contexto

```python
logger.error("msg", exc_info=True)
```

---

## Logging

```python
logger = logging.getLogger("app.module.component")
```

- Loggear entradas relevantes
- No loggear datos sensibles

---

## Testing

- Ubicación: tests/
- pytest + pytest-asyncio
- Priorizar tests de integración

Ejemplo:
```bash
uv run pytest tests/integration/test_legal_search_full_suite.py
```

---

## Git

Formato:
```
type(scope): message
```

Tipos:
- feat
- fix
- refactor
- docs
- chore

---

## AI / RAG

- Modelo principal: gpt-5.3
- Barato: gpt-4.1-mini
- Embeddings: text-embedding-3-small

Reglas:
- Mantener consistencia en queries
- Preferir búsqueda híbrida
- Evitar heurísticas frágiles

---

## Agent Rules

- Cambios mínimos y precisos
- No refactorizar sin necesidad
- No introducir abstracciones nuevas sin justificación
- Ejecutar tests tras cambios

---

## Cursor / Copilot

No se encontraron reglas específicas.
Este archivo es la referencia principal.
