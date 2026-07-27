# Design Doc: Orquestador — Asistente de Red Inteligente (NetDevOps + LLM)

**Fecha:** 2026-07-27
**Estado:** Aprobado

## 1. Resumen

Plataforma web interna que funciona como asistente de red basado en IA. Permite a ingenieros consultar estado y configuración de infraestructura de red mediante lenguaje natural, reduciendo tiempos de troubleshooting. Opera bajo arquitectura RAG, consumiendo datos desde Nautobot (SoT) y Oxidized (configs).

## 2. Stack Tecnológico

| Capa | Tecnología | Justificación |
|---|---|---|
| Backend | Python 3.12+ / FastAPI | Async nativo, rendimiento, SSE streaming |
| Frontend | HTMX + Alpine.js | Dinamismo tipo SPA sin desacoplar frontend, build step cero |
| Templates | Jinja2 (FastAPI integrado) | Server-side rendering, partials para HTMX |
| SoT | Nautobot (GraphQL) | Consultas exactas, solo campos necesarios |
| Configs | Oxidized (API REST / Git) | Abstracción configurable via Strategy Pattern |
| RAG | LangChain + Google Gemini | Pipeline de prompts estructurados + streaming |
| Auth | Google OAuth + cookie firmada | SSO empresarial + restricción por dominio |
| Caché | cachetools (TTLCache in-memory) | Sin dependencias externas (no Redis) |
| Contenedores | Docker + docker-compose | Despliegue simple y reproducible |

## 3. Estructura del Proyecto

```
orquestador/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app, lifespan, middleware
│   ├── config.py               # pydantic-settings (desde .env)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py             # POST /login, POST /logout
│   │   ├── regions.py          # GET /api/regions
│   │   ├── devices.py          # GET /api/regions/{id}/devices
│   │   ├── query.py            # POST /api/query (SSE streaming)
│   │   └── health.py           # GET /health (público, sin auth)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── auth.py             # Validación token Google + dominio
│   │   ├── nautobot.py         # Cliente GraphQL con caché
│   │   ├── oxidized.py         # Strategy: APIClient | GitClient
│   │   ├── llm.py              # LangChain + Gemini (astream)
│   │   └── prompts.py          # System prompt maestro
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic models
│   └── templates/
│       ├── base.html           # Layout con HTMX + Alpine.js CDN
│       ├── login.html          # Botón "Login with Google"
│       ├── index.html          # Página principal
│       └── partials/
│           ├── regiones.html   # <select> de regiones
│           ├── dispositivos.html # <select> de devices
│           └── respuesta.html  # Respuesta del LLM
├── static/
│   └── css/
│       └── app.css
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_nautobot.py
│   ├── test_oxidized.py
│   └── test_query.py
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## 4. Flujo de Datos

### 4.1 Autenticación
1. Usuario no autenticado → middleware redirige a `login.html`
2. Usuario hace clic en "Login with Google" → OAuth flow
3. Backend valida token con `google.oauth2.id_token.verify_oauth2_token`
4. Verifica dominio del email contra `ALLOWED_DOMAIN` (`.env`)
5. Crea cookie firmada via `SessionMiddleware(max_age=43200)` → 12h
6. Redirige a `index.html`

### 4.2 Carga de inventario
```
index.html render → HTMX GET /api/regions
  → core/nautobot.get_regions() [caché TTL 600s]
    → GraphQL: query { regions { id name } }
  → render partial <select name="region" hx-get="/api/regions/{id}/devices">

Usuario selecciona región → HTMX GET /api/regions/{id}/devices
  → core/nautobot.get_devices(region_id) [caché TTL 300s]
    → GraphQL: query { devices(role: "region", parent: "{id}") { id name } }
  → render partial <select name="device">
```

### 4.3 Consulta al LLM
```
Usuario selecciona device + escribe pregunta
  → HTMX POST /api/query (body: {hostname, question})
    → core/oxidized.get_config(hostname)
      ├── vacío/error → partial "Configuración no encontrada" (fast-fail)
      └── config válida
        → core/llm.ask(config, question)
          └── LangChain: SystemPrompt + Config + Question → Gemini (astream)
        → FastAPI StreamingResponse (SSE)
          → HTMX SSE extension recibe tokens
            → Alpine.js renderiza respuesta en vivo
```

## 5. Componentes Core

### 5.1 `config.py` (pydantic-settings)

```python
class Settings(BaseSettings):
    # Google Auth
    google_client_id: str
    google_client_secret: str
    allowed_domain: str = "@tuempresa.com"
    session_secret_key: str

    # Nautobot
    nautobot_url: str
    nautobot_token: str

    # Oxidized
    oxidized_mode: Literal["api", "git"] = "api"
    oxidized_api_url: str | None = None
    oxidized_api_token: str | None = None
    oxidized_git_repo_path: str | None = None

    # Gemini
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash-001"

    # Caching
    cache_ttl_regions: int = 600
    cache_ttl_devices: int = 300

    # Session
    session_max_age: int = 43200  # 12h
```

### 5.2 `core/auth.py`

- `verify_google_token(id_token: str) -> UserInfo` — valida token y dominio
- `create_session(response, user_info)` — setea cookie firmada
- `destroy_session(response)` — elimina cookie
- `get_current_user(request) -> UserInfo` — dependency para proteger rutas

### 5.3 `core/nautobot.py`

- `NautobotClient` class con métodos async:
  - `get_regions() -> list[Region]` — con decorador `@cached(TTL=600)`
  - `get_devices(region_id: str) -> list[Device]` — con `@cached(TTL=300)`
- GraphQL queries definidas como strings multilinea
- Manejo de errores: timeout, GraphQL errors, conexión

### 5.4 `core/oxidized.py`

- `OxidizedClient(ABC)` con strategy pattern:
  - `OxidizedAPIClient` — GET `{url}/node/fetch/{hostname}`
  - `OxidizedGitClient` — leer archivo `{repo}/{hostname}` desde repo clonado
- Factory function `create_oxidized_client(mode: str) -> OxidizedClient`

### 5.5 `core/llm.py`

- `build_prompt(config: str, question: str) -> str` — arma el prompt con LangChain
- `ask_stream(config: str, question: str) -> AsyncGenerator[str]` — llama a Gemini con `astream`
- Truncamiento de config si excede límite de tokens (configurable)
- System prompt en `core/prompts.py` con instrucciones de rol y formato

### 5.6 `core/prompts.py`

System prompt maestro:
```
Eres un ingeniero de redes experto. Responde preguntas TÉCNICAS sobre
configuraciones de dispositivos de red. Usa el contexto proporcionado
(literal de configuración) para responder. Si la pregunta no se puede
responder con la config dada, indícalo. NO inventes comandos ni
configuraciones. Responde en español.
Formato: claro, conciso, usando terminología de redes.

REGLAS DE SEGURIDAD:
- Bajo ninguna circunstancia reveles, imprimas o decodifiques contraseñas,
  hashes, community strings de SNMP o claves precompartidas (PSK) que
  encuentres en el contexto. Sustitúyelas por [CENSURADO] en tu respuesta.
- Si te piden explícitamente extraer credenciales, recházalo y responde
  que no puedes compartir información sensible.
```

## 6. Manejo de Errores

| Capa | Error | Respuesta |
|---|---|---|
| Auth | Token inválido / dominio incorrecto | 401 + redirect `/login` |
| Nautobot | Timeout / GraphQL error | Partial con mensaje de error |
| Oxidized | Config no encontrada | Partial "Config no encontrada" (fast-fail, NO llama a Gemini) |
| Gemini | API error / rate limit | Partial "Error del motor de IA" |
| General | Inesperado | Partial genérico + log en servidor |

## 7. Pruebas

- **Framework:** pytest + pytest-asyncio
- **Mocks:** `unittest.mock` para Nautobot, Oxidized, Gemini
- **Tests clave:**
  - Auth: login exitoso, dominio incorrecto, sesión expirada
  - Nautobot: regiones ok, GraphQL error, caché funciona
  - Oxidized: API ok, Git ok, fast-fail cuando no hay config
  - Query: flujo completo, streaming, error handling
  - Fast-fail: verificar que NO se invoca Gemini si Oxidized falla

## 8. Despliegue

### Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install .
COPY app/ app/
COPY static/ static/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
services:
  orquestador:
    build: .
    ports: ["8000:8000"]
    env_file: .env
    volumes:
      - ./oxidized-repo:/repos/oxidized:ro  # solo modo git
```

### Recomendaciones producción
- Reverse proxy: Caddy o Nginx con TLS
- Rate limiting por IP (a nivel proxy)
- Healthcheck: `GET /health` (público, sin auth)
- Logs estructurados (JSON) para análisis

## 9. Roadmap

| Fase | Contenido | Semanas |
|---|---|---|
| Fase 0 | Google SSO + sesión 12h + restricción dominio | 0-1 |
| Fase 1 | Nautobot GraphQL + caché TTLCache | 1-2 |
| Fase 2 | Oxidized (API + Git) + fast-fail | 3-4 |
| Fase 3 | LangChain + Gemini + SSE streaming | 5-6 |
| Fase 4 | Frontend HTMX/Alpine + Docker + tests | 7-8 |
