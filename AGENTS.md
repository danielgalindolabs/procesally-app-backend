# AGENTS.md - Procesally Backend

This document provides guidelines and commands for agents working in this codebase.

## Project Overview

- **Framework**: FastAPI with Python 3.12+
- **Database**: PostgreSQL with pgvector (vector search for AI/RAG)
- **Architecture**: Hexagonal (Clean Architecture) + DDD
- **Package Manager**: UV
- **Domain**: Legal platform with AI-powered search

## Build/Lint/Test Commands

### Using Make
```bash
make lint    # Run all linters
make test    # Run all tests
```

### Manual Commands (via UV)
```bash
# Linting (run in order)
uv run isort app              # Sort imports
uv run black app              # Format code
uv run ruff check app         # Lint with ruff
uv run flake8 app             # Additional linting

# Run single test
uv run pytest tests/path/to/test_file.py::test_function_name -v

# Run specific test file
uv run pytest tests/integration/test_legal_search_full_suite.py

# Run with coverage
uv run pytest --cov=app tests/

# Run tests matching pattern
uv run pytest -k "search" -v

# Fix ruff issues automatically
uv run ruff check app --fix
```

### Development Server
```bash
uv run fastapi run app/main.py --host 0.0.0.0 --port 8000
# Docs at: http://localhost:8000/docs
```

### Database Migrations
```bash
# Create migration
uv run alembic revision --autogenerate -m "migration name"

# Run migrations
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1
```

## Code Style Guidelines

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Files, Functions, Variables | `snake_case` | `legal_repository.py`, `get_article()` |
| Classes, Entities, Models | `PascalCase` | `ArticleEntity`, `AuthService` |
| Global Env Variables | `SCREAMING_SNAKE_CASE` | `DATABASE_URL` |

### File Naming
- Use snake_case for all Python files
- Name files after the primary class/function they contain
- Examples: `legal_repository.py`, `embedding_service.py`, `article_entity.py`

### Architecture - 4 Layers

Each module must follow this strict structure:

```
app/modules/{module_name}/
├── domain/           # Pure entities + contracts (interfaces)
│   ├── entities/     # Dataclasses with business logic
│   ├── repositories/ # Abstract repository interfaces (ABC)
│   ├── datasources/  # Abstract datasource interfaces (ABC)
│   └── services/     # Domain service interfaces (ABC)
├── application/      # Use cases (business orchestration)
│   ├── use_cases/    # One class per use case
│   └── schemas/      # Application-level DTOs
├── infrastructure/   # Concrete implementations
│   ├── repositories/ # Repository implementations
│   ├── datasources/  # Datasource implementations (SQLModel)
│   └── services/     # Service implementations
├── presentation/    # API layer
│   ├── api/          # FastAPI routers
│   ├── schemas/      # Pydantic request/response models
│   └── dependencies/ # FastAPI dependency injection
├── adapters/         # Mappers between layers
│   ├── app_domain_mapper.py
│   ├── domain_datasource_mapper.py
│   └── presentation_app_mapper.py
└── exceptions/       # Module-specific exceptions
```

### Domain Layer Rules
- **Entities** must be pure Python dataclasses
- **NO** imports from FastAPI, Pydantic, SQLAlchemy, or databases
- Only use: `dataclasses`, `typing`, standard library
- Entities define business attributes and rules

### Application Layer Rules
- **Use Cases** orchestrate business logic
- Accept domain interfaces (ABCs) in constructor
- Never import infrastructure directly
- Use application-level DTOs for input/output

### Infrastructure Layer Rules
- Implements domain interfaces
- Uses SQLModel for ORM, asyncpg for async DB access
- Contains mappers to convert between domain and datasource formats

### Presentation Layer Rules
- **Routers**: FastAPI APIRouter instances
- **Schemas**: Pydantic models for HTTP request/response
- **Dependencies**: FastAPI Depends() functions for DI

### Imports Organization
```python
# 1. Standard library
import logging
import re
from typing import List, Optional

# 2. Third-party (separated by blank line)
from fastapi import APIRouter, Depends

# 3. Local imports - absolute paths with line continuation
from app.modules.legal_library.adapters.app_domain_mapper import \
    AppDomainMapper
from app.modules.legal_library.application.schemas.article_app_schemas import \
    ArticleAppOutputDTO
```

### Type Annotations
- **Required** for all function parameters and return types
- Use `Optional[X]` instead of `X | None`
- Use `List[X]`, `Dict[X, Y]` (not lowercase versions)

### Error Handling
- Create custom exceptions in `exceptions/` directory
- Use inheritance from base exceptions
- Log errors with appropriate context
- Return proper HTTP status codes in routers

### Logging Pattern
```python
import logging

logger = logging.getLogger("app.module_name.component")
```

### Docstrings
- Use docstrings for all public classes and methods
- Follow Google style or simple descriptive text
- Document purpose, not implementation details

### Testing
- Test files go in `tests/` directory
- Naming: `test_*.py`
- Use `pytest` with `pytest-asyncio`
- Test configuration in `pyproject.toml`

## Git Conventions (Conventional Commits)

Format: `type(layer): description`

Types:
- `feat`: New endpoints, entities, or use cases
- `fix`: Bug fixes
- `refactor`: Code reorganization without behavior change
- `docs`: Documentation changes
- `chore`: Dependencies, infrastructure, tooling

Example: `feat(legal_library): add vector search use case`

## Configuration

### Configuration Files Location
All configuration files are in `app/core/`:
- `config.py` - Application settings (env variables)
- `legal_laws.yaml` - Law mappings and keywords for legal search
- `legal_config.py` - Loader for legal_laws.yaml

### Legal Laws Configuration (`app/core/legal_config.py`)
Este archivo Python contiene todos los diccionarios hardcodeados para la búsqueda legal:

```python
LAW_MAPPINGS = {
    "CODIGO CIVIL FEDERAL": "CÓDIGO CIVIL FEDERAL",
    "TRABAJO": "Ley Federal del Trabajo",
    # Añadir nuevas leyes aquí...
}

SEMANTIC_KEYWORDS = [
    "explica",
    "relacion",
    "interpretación",
    # ...
]

NUMBER_WORDS = {
    "uno": "1",
    "dos": "2",
    # ...
}
```

**Para agregar/modificar leyes o keywords**: Editar `app/core/legal_config.py`.

### Environment Variables
Settings loaded from `.env` file:
- `POSTGRES_*` - Database connection
- `OPENAI_API_KEY` - AI API key
- `EMBEDDING_MODEL_NAME` - Embedding model (default: text-embedding-3-small)

## Settings
- **Max line length**: 150 characters
- **Python version**: 3.12+
- **Async mode**: `asyncio_mode = "auto"` for tests
- **Test path**: `tests/`
- **Linters**: ruff, flake8, black, isort
