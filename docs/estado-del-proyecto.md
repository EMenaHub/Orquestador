# Orquestador — Estado del Proyecto

**Versión:** 0.1.0  
**Repositorios:**
- GitHub EMenaHub: `git@github.com:EMenaHub/Orquestador.git`
- GitHub TioMena: `git@github.com:TioMena/Orquestador.git`

---

## Resumen

Orquestador es un asistente de red inteligente (NetDevOps + LLM) que permite a ingenieros de red consultar configuraciones de dispositivos usando lenguaje natural. Obtiene los dispositivos desde **Nautobot** (SoT), las configuraciones desde **Oxidized** y utiliza una instancia privada de **OpenWebUI** (API compatible con OpenAI) como LLM para responder preguntas técnicas sobre las configuraciones.

---

## Stack Tecnológico

| Componente | Tecnología |
|---|---|
| Backend | Python 3.12+, FastAPI |
| Frontend | HTMX 2.x + Alpine.js 3.x |
| Source of Truth | Nautobot (GraphQL) |
| Configuraciones | Oxidized (API REST / Git) |
| LLM | OpenWebUI (OpenAI-compatible) via LangChain |
| Autenticación | Google OAuth (dominio @zapping.com) |
| Sesiones | Starlette SessionMiddleware (12h) |
| Cache | cachetools TTLCache |
| Tests | pytest + httpx AsyncClient |
| Contenerización | Docker / docker-compose |

---

## Arquitectura

```
Usuario (browser)
    │
    ├── /auth/login → Google OAuth → callback → sesión
    │
    ├── GET / → index.html (HTMX + Alpine)
    │       └── hx-get /api/tenants → partials/tenants.html
    │               ├── Nautobot GraphQL → devices por tenant
    │               └── Inyecta dispositivos manuales faltantes
    │
    ├── POST /api/query
    │       ├── Oxidized → fetch config
    │       ├── LangChain + OpenWebUI → respuesta streaming
    │       └── SSE → respuesta.html
    │
    └── GET /api/config/{hostname}
            └── Oxidized → raw config (texto plano)
```

### Flujo de consulta LLM

1. Usuario selecciona un dispositivo y escribe una pregunta
2. Backend obtiene la configuración desde Oxidized
3. La configuración se pasa como contexto a OpenWebUI via LangChain (ChatOpenAI)
4. La respuesta se stremea al frontend via Server-Sent Events (SSE)
5. El frontend renderiza la respuesta en tiempo real

### Seguridad en el prompt

El system prompt del LLM tiene reglas estrictas:
- No revelar contraseñas, hashes, SNMP community strings ni PSK
- No inventar información que no esté en el contexto
- Responder solo con la configuración proporcionada
- Respuestas en español, con terminología de redes

---

## Estado Actual

### ✅ Completado

**Infraestructura base**
- Proyecto FastAPI con configuración via pydantic-settings
- Dockerfile + docker-compose.yml
- 25 tests unitarios y de integración pasando

**Autenticación**
- Google OAuth login/callback/logout
- Restricción por dominio `@zapping.com`
- Sesión con cookie firmada (12h de duración)
- Modo HTTP local (sin HTTPS) via `SESSION_HTTPS_ONLY=false`

**Nautobot (Source of Truth)**
- Cliente GraphQL con caché (TTL configurable)
- Query con `limit: 500` para obtener todos los dispositivos
- Filtro por roles configuravble en `.env`
- 4 tenants con dispositivos agrupados

**Oxidized (Configuraciones)**
- Cliente API REST funcional
- Verificado: `CL-DC2-CORE-1` retorna 181KB de config (Huawei NetEngine 8000)
- Strategy pattern: soporta modo `api` y modo `git`

**LLM Pipeline**
- LangChain con `ChatOpenAI` (OpenWebUI)
- System prompt con reglas de seguridad
- Truncamiento de configuraciones largas (>30K tokens)
- Streaming SSE para respuestas en tiempo real

**Frontend**
- Tabs Alpine.js por tenant
- Selector de dispositivos por tab
- Formulario de consulta con loading state
- Respuesta streaming vía HTMX SSE

**Dispositivos**
- 17 dispositivos obtenidos desde Nautobot (roles: CORE, ROUTER, VPN, AGG, ACC, SWITCH)
- 7 dispositivos inyectados manualmente (no existen en Nautobot)

### ❌ Pendiente / Bloqueado

| Ítem | Estado | Detalle |
|---|---|---|
| **OpenWebUI API Key** | 🔴 Bloqueado | `.env` tiene `OPENWEBUI_API_KEY` pendiente. Sin esto el LLM no funciona. |
| **Consulta LLM end-to-end** | 🔴 Bloqueado | Depende de la API Key de OpenWebUI. |
| **Dispositivos faltantes en Nautobot** | 🟡 Workaround | 7 dispositivos se inyectan manualmente en código. Solución ideal: crearlos en Nautobot. |
| **Investigación Nautobot** | 🟡 Pendiente | Hay 242 dispositivos en Nautobot pero muchos no tienen el rol esperado o no tienen tenant asignado. |
| **Oxidized mode=git** | 🟡 No probado | Solo se ha probado con `OXIDIZED_MODE=api`. El modo git no se ha validado. |
| **Logging / monitoreo** | ⬜ No iniciado | No hay logs estructurados ni métricas. |
| **Manejo de errores en Oxidized** | ⬜ No iniciado | Algunos dispositivos podrían no tener configuración en Oxidized (404). |
| **Rate limiting** | ⬜ No iniciado | No hay límite de consultas por usuario. |
| **Prueba con dispositivos reales** | 🟡 Parcial | Solo se probó con CL-DC2-CORE-1 en Oxidized. |
| **Despliegue en producción** | ⬜ No iniciado | Docker build y ejecución no probada fuera de localhost. |
| **Documentación de usuario** | ⬜ No iniciado | Falta guía de uso para ingenieros. |
| **CI/CD** | ⬜ No iniciado | Sin pipeline de integración continua. |

---

## Dispositivos Disponibles

### Zapping Chile (13 dispositivos)

| Dispositivo | Rol | Origen |
|---|---|---|
| CL-DC1-ACC-1 | ACC | Nautobot |
| CL-DC1-AGG-1 | AGG | Nautobot |
| CL-DC1-AGG-2 | AGG | Nautobot |
| CL-DC1-CORE-1 | CORE | Nautobot |
| CL-DC1-VPN-1 | VPN | Nautobot |
| CL-DC2-AGG-1 | AGG | Nautobot |
| CL-DC2-CORE-1 | CORE | Nautobot |
| CL-DC2-VPN-1 | VPN | Nautobot |
| Router Huawei | — | Nautobot |
| SDWAN | — | Nautobot |
| CL-DC1-AGG-3 | AGG | Manual |
| CL-DC2-AGG-2 | AGG | Manual |
| CL-OFF-RT-1 | ROUTER | Manual |

### Zapping Brasil (10 dispositivos)

| Dispositivo | Rol | Origen |
|---|---|---|
| BR-CB-EDGE-1 | SWITCH | Nautobot |
| BR-DC1-CORE-1 | CORE | Nautobot |
| BR-DC1-VPN-1 | VPN | Nautobot |
| BR-DC2-CORE-1 | CORE | Nautobot |
| BR-DC2-VPN-1 | VPN | Nautobot |
| BR-DC3-VPN-1 | VPN | Nautobot |
| BR-ION-VPN-1 | VPN | Nautobot |
| BR-CB-VPN-1 | VPN | Manual |
| BR-DC2-VPN-2 | VPN | Manual |
| BR-ION-EDGE-1 | SWITCH | Manual |

### Zapping Ecuador (5 dispositivos)

| Dispositivo | Rol | Origen |
|---|---|---|
| EC-DC1-CORE-1 | CORE | Nautobot |
| EC-DC1-VPN-1 | VPN | Nautobot |
| EC-DC2-CORE-1 | CORE | Nautobot |
| EC-DC2-VPN-1 | VPN | Nautobot |
| EC-EV-EDGE | SWITCH | Manual |

### Zapping Peru (4 dispositivos)

| Dispositivo | Rol | Origen |
|---|---|---|
| PE-DC1-CORE-1 | CORE | Nautobot |
| PE-DC1-VPN-1 | VPN | Nautobot |
| PE-LATINA-VPN-1 | VPN | Nautobot |
| VPN-PE-LA-1 | VPN | Nautobot |

---

## Cómo Ejecutar

### Local (desarrollo)

```bash
# 1. Crear y activar virtualenv
python3.12 -m venv .venv && source .venv/bin/activate

# 2. Instalar dependencias
pip install -e .[dev]

# 3. Configurar .env (ver .env.example)
#    ⚠️ OPENWEBUI_API_KEY es obligatorio para consultas LLM

# 4. Ejecutar
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 5. Tests
python -m pytest tests/ -v
```

### Docker

```bash
docker compose up --build
```

---

## Variables de Entorno (.env)

| Variable | Descripción | Requerido |
|---|---|---|
| `GOOGLE_CLIENT_ID` | Client ID de Google OAuth | Sí |
| `GOOGLE_CLIENT_SECRET` | Client Secret de Google OAuth | Sí |
| `ALLOWED_DOMAIN` | Dominio permitido para login | Sí |
| `SESSION_SECRET_KEY` | Clave para firmar cookies de sesión | Sí |
| `NAUTOBOT_URL` | URL base de Nautobot | Sí |
| `NAUTOBOT_TOKEN` | Token de API de Nautobot | Sí |
| `NAUTOBOT_DEVICE_ROLES` | Roles permitidos (separados por coma) | Sí |
| `OPENWEBUI_API_KEY` | API Key de OpenWebUI | Sí (para LLM) |
| `OPENWEBUI_BASE_URL` | URL base de OpenWebUI (ej: `http://openwebui.internal.cl/v1`) | Sí (para LLM) |
| `OPENWEBUI_MODEL` | Modelo a usar (ej: `mistral`, `llama3`) | Sí (para LLM) |
| `OXIDIZED_API_URL` | URL base de Oxidized API | Sí (modo api) |
| `SESSION_HTTPS_ONLY` | `false` para HTTP local | Desarrollo |

---

## Notas Técnicas

### Filtro de roles

El filtro `NAUTOBOT_DEVICE_ROLES` define qué roles de dispositivo se muestran en la UI. Actualmente: `CORE,ROUTER,VPN,AGG,ACC,SWITCH`. Nautobot tiene 242 dispositivos totales pero muchos tienen roles como CDN, ENC, DECODER, APIC, etc. que están fuera del filtro.

### Dispositivos manuales

7 dispositivos no existen en Nautobot pero están hardcodeados en `app/core/nautobot.py`:

| Dispositivo | Tenant | Razón probable |
|---|---|---|
| BR-CB-VPN-1 | Brasil | No creado en Nautobot |
| BR-DC2-VPN-2 | Brasil | No creado en Nautobot |
| BR-ION-EDGE-1 | Brasil | No creado en Nautobot |
| CL-DC1-AGG-3 | Chile | No creado en Nautobot |
| CL-DC2-AGG-2 | Chile | No creado en Nautobot |
| CL-OFF-RT-1 | Chile | No creado en Nautobot |
| EC-EV-EDGE | Ecuador | No creado en Nautobot |

**Solución ideal:** Crear estos dispositivos en Nautobot con los roles y tenant correspondientes.

---

## Próximos Pasos Recomendados

1. **Configurar OpenWebUI** — Colocar `OPENWEBUI_API_KEY`, `OPENWEBUI_BASE_URL` y `OPENWEBUI_MODEL` en `.env`
2. **Completar dispositivos en Nautobot** — Crear los 7 dispositivos faltantes para eliminar el hardcode
3. **Revisar roles en Nautobot** — Validar que todos los dispositivos tengan el rol correcto y tenant asignado
4. **Probar consultas reales** — Con Gemini funcionando, probar preguntas sobre configuraciones reales
5. **Agregar logging** — Implementar logs estructurados para debugging
6. **Preparar deploy** — Docker build, CI/CD, y despliegue en servidor de producción
