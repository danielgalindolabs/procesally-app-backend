# Procesally Backend API

![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111%2B-009688?logo=fastapi)
![SQLModel](https://img.shields.io/badge/SQLModel-0.0.21-3e827a)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-336791?logo=postgresql)

El núcleo backend de Procesally. Provee la infraestructura de red, el motor de Inteligencia Artificial (RAG) basado en búsquedas vectoriales y el esquema de seguridad global del sistema.

Construido para operar bajo altos niveles de concurrencia mediante operaciones I/O 100% asíncronas, y organizado bajo los principios de **Arquitectura Limpia (Hexagonal)** y **Diseño Dirigido por Dominio (DDD)**.

## 🛠 Tech Stack

- **Framework Web**: [FastAPI](https://fastapi.tiangolo.com/)
- **ORM & Database**: [SQLModel](https://sqlmodel.tiangolo.com/) + PostgreSQL (`pgvector`)
- **Driver DB Asíncrono**: `asyncpg`
- **Package Manager**: [UV](https://github.com/astral-sh/uv)
- **Quality & Testing**: Pytest + pytest-asyncio + Httpx
- **Despliegue (Ops)**: Docker Multi-stage

## 🏗 Arquitectura del Sistema

El proyecto sigue una estricta separación de responsabilidades dividida en sub-dominios funcionales (ej. `auth`, `users`, `legal_library`). Cada módulo interno se compone invariablemente de 4 capas protectoras:

1. **`domain/`**: Entidades core y contratos (Interfaces de Repositorios/Datasources). Máximo nivel de abstracción; agnosticismo total frente a frameworks externos.
2. **`application/`**: Casos de Uso (Orquestadores de la lógica de negocio).
3. **`infrastructure/`**: Implementaciones concretas de la base de datos, APIs de terceros y frameworks de manipulación de datos (`SQLModel`, `asyncpg`).
4. **`presentation/`**: Capa de exposición al cliente expuesta como micro-enrutadores (`api/`), Modelos de Transferencia de Datos/DTOs (`schemas/`) e inyecciones de conexión HTTP (`dependencies/`).

*Nota: Consulta el esquema visual nativo en `/docs/architecture_diagram.xml` (importable en Draw.io).*

---

## ⚙️ Instrucciones de Desarrollo Local

### Requisitos Previos
- **Python 3.12+**
- **UV** (Recomendado instalar vía `brew install uv` en macOS).
- **PostgreSQL** corriendo localmente con la extensión `pgvector` instalada.

### Aprovisionamiento del Entorno
1. Clonar este repositorio y navegar a la raíz del proyecto.
2. Definir las variables ambientales creando (o modificando) el archivo maestro `.env` asegurando la correcta inyección de la cadena de base de datos.
3. Sincronizar automáticamente el entorno y las dependencias estandarizadas a través del gestor:
   ```bash
   uv sync
   ```

### Ejecutar el Servidor
Lanza el entorno de exposición de FastAPI internamente orquestado por el intérprete aislado:
```bash
uv run fastapi run app/main.py --host 0.0.0.0 --port 8000
```
La documentación interactiva autogenerada estándar será inyectada en: `http://localhost:8000/docs`.

### Integración Continua (Testing)
Para corroborar la integridad de la asincronicidad y asersión en la inyección de dependencias correr la Suite interna:
```bash
uv run pytest
```

---

## 🐳 Despliegue con Docker (Producción)

El proyecto cuenta con un `Dockerfile` optimizado (Multi-stage build) que aprovecha la naturaleza de capas indexables de Docker en conjunción con la sincronización congelada binaria de `uv` (`uv.lock`) para generar contenedores ultraligeros exentos de dependencias de desarrollo.

1. **Construir la imagen nativa:**
   ```bash
   docker build -t procesally-api:latest .
   ```
2. **Ejecutar el contenedor:**
   ```bash
   docker run -d -p 8000:8000 --env-file .env procesally-api:latest
   ```

---

## 📏 Convenciones Constructivas (Lineamientos PEP 8)
Para asegurar el escalamiento vertical colaborativo se estandarizan las siguientes normas de sintaxis:

- **Archivos, Funciones y Variables**: `snake_case` (ej. `legal_repository.py`, `get_article()`).
- **Clases, Entidades Puras y Modelos**: `PascalCase` (ej. `LegalArticle`, `AuthService`).
- **Variables Globales (.env y Configuración)**: `SCREAMING_SNAKE_CASE` (ej. `DATABASE_URL`).

## 🚀 Estándar Git (Conventional Commits)
El rastro de evolución de Git (History) será semánticamente ordenado mediante la sintaxis imperativa: 
`tipo(capa_afectada): descripcion_corta`

**Tipos Reconocidos por la Arquitectura:**
- `feat`: Adición de endpoints, entidades o lógicas en casos de uso.
- `fix`: Corrección de defectos en flujos vivos.
- `refactor`: Reorganización profunda sin alteración externa en testing iterativo.
- `docs`: Intervención en documentación de sistema abstracta.
- `chore`: Tareas de construcción, mantenimiento de librerías, actualización de `uv` o infraestructura.
