
# Arquitectura de API – Procesally (Primera Versión)

La plataforma **Procesally** está diseñada bajo un enfoque de **módulos funcionales independientes**. Cada módulo expone sus propios endpoints para garantizar escalabilidad, modularidad y facilidad de mantenimiento.

---

## 1. Módulo de Usuarios

*Gestión de registro, autenticación y perfiles.*

### Endpoints Conceptuales

* **Crear cuenta:** `POST /users/register` - Registro de nuevos usuarios y validación de correo.
* **Iniciar sesión:** `POST /auth/login` - Validación de credenciales y generación de tokens.
* **Cerrar sesión:** `POST /auth/logout` - Invalidación de tokens de sesión.
* **Obtener perfil:** `GET /users/me` - Consulta de información, plan de suscripción e historial.
* **Actualizar perfil:** `PATCH /users/me` - Modificación de datos personales y preferencias.
* **Consultar suscripción:** `GET /users/me/subscription` - Verificación de nivel de acceso (Free/Premium).
* **Historial de documentos:** `GET /users/me/documents` - Lista de documentos generados por el usuario.

---

## 2. Módulo de Biblioteca de Plantillas

*Catálogo de documentos legales disponibles.*

### Endpoints Conceptuales

* **Listar plantillas:** `GET /templates` - Filtros por materia jurídica, tipo y categoría.
* **Detalles de plantilla:** `GET /templates/{id}` - Estructura, campos editables y versiones.
* **Buscar plantillas:** `GET /templates/search` - Búsqueda por palabras clave.
* **Descargar plantilla:** `GET /templates/{id}/download` - Obtención del archivo base según el plan.
* **Generar documento:** `POST /templates/{id}/generate` - Crea una copia editable (conecta con el Editor).
* **Listar categorías:** `GET /templates/categories` - Materias disponibles (Civil, Penal, Laboral, etc.).

---

## 3. Módulo de Editor de Documentos

*Edición y gestión de documentos personalizados.*

### Endpoints Conceptuales

* **Crear documento:** `POST /editor/documents` - Clona una plantilla para edición.
* **Obtener documento:** `GET /editor/documents/{id}` - Recupera contenido y estructura actual.
* **Guardar cambios:** `PUT /editor/documents/{id}` - Guardado de versiones y persistencia.
* **Exportar:** `POST /editor/documents/{id}/export` - Generación en PDF, Word o Texto.
* **Eliminar:** `DELETE /editor/documents/{id}` - Borrado lógico o físico del documento.
* **Listar documentos:** `GET /editor/documents` - Listado general de archivos del usuario.

---

## 4. Módulo de Biblioteca Legal

*Acceso a material jurídico público y legislación.*

### Endpoints Conceptuales

* **Listar material:** `GET /legal-library` - Acceso a leyes, reglamentos y códigos.
* **Obtener contenido:** `GET /legal-library/{id}` - Consulta por capítulos o artículos específicos.
* **Buscar legislación:** `GET /legal-library/search` - Búsqueda semántica o por palabra clave.
* **Listar fuentes:** `GET /legal-library/sources` - Origen de datos (DOF, bibliotecas públicas).
* **Estructura de ley:** `GET /legal-library/{id}/structure` - Jerarquía de títulos y capítulos.

---

## 5. Módulo de Eventos y Logging

*Sistema interno de monitoreo, auditoría y métricas.*

### Endpoints Conceptuales

* **Registrar evento:** `POST /logs/events` - Registro de acciones (login, descargas, errores).
* **Consultar logs:** `GET /logs` - Filtros por tipo de evento, usuario y fecha.
* **Estadísticas:** `GET /logs/metrics` - Análisis de uso (plantillas más usadas, actividad).

---

## 6. Módulo de Seguridad y Autorización

*Control de acceso y validación de permisos.*

### Endpoints Conceptuales

* **Validar token:** `POST /auth/verify` - Verificación de vigencia del token.
* **Renovar token:** `POST /auth/refresh` - Extensión de la sesión activa.
* **Verificar permisos:** `GET /auth/permissions` - Validación de acceso a recursos Premium.
* **Revocar sesión:** `DELETE /auth/sessions/{id}` - Cierre forzado de sesiones.

---

## Características Técnicas

### Organización del Proyecto

La estructura sugerida para el backend (ej. FastAPI) es por dominios:

```text
modules/
├── users/           # Perfiles y cuentas
├── templates/       # Catálogo legal
├── editor/          # Lógica de edición
├── legal_library/   # Legislación
├── logging/         # Auditoría
└── auth/            # Seguridad
```
