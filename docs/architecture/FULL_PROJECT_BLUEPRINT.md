# PLANO MAESTRO DEL PROYECTO: VICTORIA VOICE ORCHESTRATOR
**Nivel de Detalle**: Exhaustivo (File-by-File, Dependencias, Ramas, Capas)
**Arquitectura Backend**: Hexagonal (Puertos y Adaptadores) Estricta
**Arquitectura Frontend**: React + Redux Toolkit (Slices) + Feature-Based Structure

---

## 🏗️ 1. ESTRATEGIA DE REPOSITORIO Y RAMAS (GIT)
El proyecto utiliza un modelo de ramas tipo **GitFlow / Trunk-Based Development**:
- `main` / `master`: Código estable, desplegado en Producción.
- `develop` / `staging`: Entorno de pre-producción (Pruebas E2E y de Integración).
- `feature/*`: Desarrollo de nuevas características (ej. `feature/azure-tts-integration`).
- `bugfix/*` o `hotfix/*`: Corrección de errores (ej. `hotfix/ws-audio-memory-leak`).
- `audit/*`: Ramas temporales usadas durante la auditoría de refactorización (ej. `audit/phase-a-domain`).

---

## 📦 2. DEPENDENCIAS ESTRUCTURALES

### Backend (`backend/requirements.txt`)
**Core & Servidor**:
- `fastapi>=0.100.0` (Framework API REST y WebSocket)
- `uvicorn[standard]>=0.23.0` (Servidor ASGI)
- `pydantic>=2.0.0` & `pydantic-settings` (Validación de esquemas y configuración)

**Base de Datos**:
- `SQLAlchemy>=2.0.0` (ORM Core y Async)
- `aiosqlite` / `asyncpg` (Drivers asíncronos para DB)
- `alembic` (Migraciones, Fase 20)

**IA & Audio (Adaptadores)**:
- `groq>=0.4.0` (LLM de baja latencia)
- `openai>=1.0.0` (LLM alternativo)
- `azure-cognitiveservices-speech` (TTS y STT)

**Infraestructura & Seguridad**:
- `redis>=5.0.0` (Caché y PubSub)
- `slowapi` (Rate Limiting)
- `prometheus-fastapi-instrumentator` (Métricas)
- `sentry-sdk` (Error Tracking)

### Frontend (`frontend/package.json`)
**Core & UI**:
- `react`, `react-dom` (v18+)
- `vite` (Bundler y entorno de desarrollo)
- `tailwindcss`, `postcss`, `autoprefixer` (Estilos)

**Estado & Datos**:
- `@reduxjs/toolkit`, `react-redux` (Manejo de estado global)
- `axios` (Cliente HTTP)

**Audio & Multimedia**:
- Uso de APIs nativas: `MediaRecorder`, `AudioContext`, `WebSocket`.

---

## 🏛️ 3. PLANO EXHAUSTIVO DEL DIRECTORIO (FILE-BY-FILE)

### 📂 RAÍZ DEL PROYECTO (DevOps, Configuración Global)
- `docker-compose.dev.yml`: Orquestador de contenedores para desarrollo local (incluye Redis, DB).
- `docker-compose.prod.yml`: Orquestador para producción (redes aisladas, volúmenes persistentes).
- `.gitignore`: Ignora `node_modules/`, `__pycache__/`, `.venv/`, `.env.local`, coberturas de test.
- `README.md`: Visión general del proyecto.
- `pytest.ini`: Configuración de la suite de pruebas asíncronas de Python.
- `alembic.ini`: Configuración de migraciones de base de datos.

#### 📂 `.github/workflows/` (CI/CD GitHub Actions)
- `ci.yml`: Integración continua (Lint, Pytest unitarios e integrados al hacer PR).
- `cd-staging.yml`: Despliegue a entorno Staging.
- `cd-production.yml`: Despliegue manual a Producción.

#### 📂 `config/environments/` (Gestión de Entornos)
- `.env.example`: Plantilla de variables de entorno requeridas.
- `.env.local`: Variables reales para entorno local de desarrollador (Ignorado en git).

#### 📂 `docs/` (Documentación del Sistema)
- `architecture/ARCHITECTURE.md`: Declaración formal de la Arquitectura Hexagonal.
- `architecture/BLUEPRINTS.md`: Diagramas Mermaid de flujo y topología.
- `deployment/CHECKLIST.md`: Pasos para pasar a paso a Producción.
- `deployment/ROLLBACK.md`: Planes de mitigación y recuperación de desastres.
- `deployment/SECRETS.md`: Gestión de credenciales seguras.
- `development/SETUP.md`: Guía de onboarding para nuevos desarrolladores.
- `monitoring/GRAFANA.md`, `LOGGING.md`, `TRACING.md`: Políticas de observabilidad.
- `audit/`: Historial de todo el proceso de refactorización hacia Hexagonal (Fases A a J).

---

### 🧱 4. BACKEND (Arquitectura Hexagonal Estricta)
Ruta: `Victoria/backend/`

#### 🟢 4.1 DOMAIN `backend/domain/`
*Cero dependencias externas. Contiene el ADN del negocio.*
- **📂 `value_objects/`** (Primitivas inmutables):
  - `call_id.py`: Identificador tipado para llamadas.
  - `phone_number.py`: Validación E.164.
  - `voice_config.py`: Definición de Voz (Azure/ElevenLabs, velocidad, pitch).
  - `conversation_turn.py`: Un turno de diálogo (timestamp, rol, contenido).
- **📂 `entities/`** (Reglas de negocio puro y estado de mutación):
  - `call.py`: Entidad Raíz. Gestiona el ciclo de vida de la llamada (status, start, end).
  - `agent.py`: Entidad que define el prompt base, first message y configuración de voz de la IA.
  - `conversation.py`: Agrupador de turnos de diálogo y generador de transcripciones (formatos LLM).
- **📂 `ports/`** (Interfaces Abstractas. Contratos que la infraestructura debe cumplir):
  - `llm_port.py`, `stt_port.py`, `tts_port.py`: Servicios Cognitivos.
  - `telephony_port.py`: Controlador de conexiones SIP/PSTN.
  - `persistence_port.py`: Repositorios (`CallRepository`, `AgentRepository`).
- **📂 `use_cases/`** (Servicios de aplicación de dominio puro):
  - `start_call.py`: Orquesta la creación de `Call` y asigna `Agent`.
  - `end_call.py`: Finaliza la llamada y cierra el registro.
  - `generate_response.py`: Flujo lógico: "Input de STT -> History a LLM -> Texto a TTS".

#### 🟡 4.2 APPLICATION `backend/application/`
*Sin reglas de negocio. Orquesta la ejecución y compone los puertos.*
- **📂 `services/`**:
  - `call_orchestrator.py`: El "cerebro" en runtime. Conecta el WebSocket, inyecta dependencias reales en los casos de uso, captura audio, detiene TTS cuando el usuario interrumpe (VAD).
- **📂 `factories/`**:
  - `orchestrator_factory.py`: Ensambla el `CallOrchestrator` inyectando los adaptadores correspondientes según el `tenant`/`agente`.
- **📂 `processors/`**:
  - Componentes stateless para pipeline: `vad_processor.py` (Detección de voz), `audio_buffer.py` (Gestión de frames de audio).

#### 🔴 4.3 INFRASTRUCTURE `backend/infrastructure/`
*El mundo exterior. Dependencias técnicas (APIs, Bases de datos).*
- **📂 `adapters/`** (Implementaciones reales de los Puertos):
  - `llm/groq_adapter.py`: Integración API de Groq (Llama-3).
  - `tts/azure_tts_adapter.py`: SDK de Microsoft Cognitive Services para Síntesis.
  - `stt/azure_stt_adapter.py`: SDK de Microsoft para Transcripción STT.
- **📂 `database/`** (SQLAlchemy genérico para SQLite o PG):
  - `session.py`: Generador de `AsyncSession`.
  - `models.py`: Modelos ORM (`CallModel`, `AgentModel`, `TranscriptModel`).
  - `repositories/sqlalchemy_repositories.py`: Implementan `persistence_port.py` (lectura/escritura en BD).
- **📂 `config/`**:
  - `settings.py`: `BaseSettings` (Pydantic) para mapeo seguro de `.env`.
  - `features.py`: Lógica de Feature Flags.
- **📂 `security/`**:
  - `core.py`: Autenticación de API Key (`X-API-Key`) y Rate Limiting (`slowapi`).
  - `headers.py`: Middleware ASGI para inyección de CSP, HSTS, X-Frame-Options.
- **📂 `monitoring/`**:
  - `metrics.py`: Instanciación de contadores e histogramas Prometheus propios (`victoria_call_duration_seconds`).
  - `sentry.py`: Integración con Sentry.io.
- **📂 `logging/`**:
  - `config.py`: Salida JSON estructurada inyectando UUID correlativo (`Request-ID`).

#### 🔵 4.4 INTERFACES `backend/interfaces/`
*Puntos de entrada al sistema (FastAPI).*
- **📂 `http/`** (API REST Completa):
  - `main.py`: Punto de entrada ASGI. Registra Middlewares, routers y ciclo de vida de FastAPI.
  - `deps.py`: Inyección de dependencias de FastAPI (DB Sessions, Repositorios).
  - **📂 `endpoints/`**:
    - `config.py`: CRUD protegido para configuración de agentes e interfaces (Opciones de TTS, Idiomas).
    - `history.py`: Paginación y visualización del historial de llamadas (Protegido).
    - `telephony.py`: Webhooks públicos (Ej. `/webhook/twilio/status`) para control asincrónico.
    - `health.py`: Liveness y Readiness probes.
  - **📂 `schemas/`**: Pydantic models para Request/Response bodies (DTOs de entrada).
- **📂 `websocket/`**:
  - **📂 `endpoints/`**:
    - `audio_stream.py`: Controlador bidireccional de tiempo real (Browser Mic -> WS -> Orchestrator -> WS -> Browser Speaker).

---

### ⚛️ 5. FRONTEND (Arquitectura basada en Features)
Ruta: `Victoria/frontend/`
*Aplicación SPA (Single Page Application) construida en React 18 / TypeScript.*

#### 📂 Configuración del Frontend
- `index.html`: Punto de entrada del navegador.
- `vite.config.ts`: Configuración de empaquetado y alias de rutas (`@/`).
- `tailwind.config.js` / `postcss.config.js`: Diseño utilitario.
- `.env`, `.env.test`: Variables de entorno cliente (Ej. `VITE_API_URL`).

#### 📂 `src/` (Código fuente principal)
- `main.tsx`: Renderizado principal y proveedor del Store (`<Provider store={store}>`) y Router (`<RouterProvider>`).
- `App.tsx`: Layout base global de la aplicación.

- **📂 `store/`** (Redux Toolkit - Estado Global):
  - `store.ts`: Configuración del almacén (root reducer, middleware).
  - **📂 `slices/`**: Lógica de estado aislada por dominio.
    - `uiSlice.ts`: Estado puramente visual (Theme, Sidebar open/closed, Toasts, Modales).
    - `authSlice.ts`: Estado local de acceso/sesión.
    - `configSlice.ts`: Carga asíncrona de las opciones del Agente y Voces (Thunks).
    - `callsSlice.ts`: Gestión asíncrona y caché del Historial de Llamadas.

- **📂 `services/`** (API Clients):
  - `api.ts`: Instancia de Axios preconfigurada con Interceptors (manejo de errores genéricos, inyección del secret en headers si aplica).
  - `configService.ts`: Llamadas a `/api/config/*` del backend.
  - `historyService.ts`: Llamadas a `/api/history/*` del backend.
  - `telephonyService.ts`: Servicios para webhooks o estatus externos.

- **📂 `components/`** (Bloques visuales):
  - **📂 `common/`** (UI Atómico y reutilizable en todo el proyecto):
    - `Button.tsx`, `Card.tsx`, `Input.tsx`, `Select.tsx`, `Badge.tsx`, `Spinner.tsx`.
  - **📂 `layout/`** (Estructura visual macro):
    - `Sidebar.tsx`, `Header.tsx`, `MainContent.tsx`.
  - **📂 `features/`** (Componentes Smart atados a Slices o Lógica de Negocio):
    - **📂 `Simulator/`**:
      - `SimulatorPanel.tsx`: Envuelve el cliente WS del navegador.
      - `AudioVisualizer.tsx`: Ondas de audio en tiempo real usando Web Audio API.
      - `hooks/useSimulator.ts`: Hook que encapsula toda la interacción WebSocket y estado del MediaRecorder.
      - `utils/audioContext.ts`: Puente para transcodificar audio del micro a PCM16 (requerido por Backend WS).
    - **📂 `Config/`**:
      - `AgentConfigForm.tsx`, `VoiceSelector.tsx`, `PromptEditor.tsx`.
    - **📂 `History/`**:
      - `HistoryTable.tsx`, `CallDetailsModal.tsx`, `TranscriptViewer.tsx`.

- **📂 `pages/`** (Vistas enrutadas principales):
  - `DashboardPage.tsx`: Vista general interactiva y métricas.
  - `VoiceConfigPage.tsx`: Edición de propiedades de IA.
  - `CallHistoryPage.tsx`: Visor de base de datos.

- **📂 `hooks/`** (Utilitarios de React compartidos):
  - `useAppSelector.ts` / `useAppDispatch.ts`: Hooks tipados de Redux.
  - `useToast.ts`: Gestor de notificaciones UI.

- **📂 `types/`** (Modelos de datos Tipados de TypeScript):
  - `index.ts`: Definición de interfaces compatibles estrictamente con los DTOs de Backend Pydantic (ej. `Call`, `AgentConfig`, `VoiceConfig`).

---

### 🧪 6. SUITES DE PRUEBAS AUTOMATIZADAS
Ruta: `Victoria/tests/` (Backend) y `Victoria/frontend/src/**/__tests__/` (Frontend).

- **Backend (Pytest)**:
  - `tests/unit/`: Verificación aislada de módulos del Dominio y VAD processor (Mocks al 100%).
  - `tests/integration/`: Pruebas de repositorios utilizando BBDD en memoria SQLite Async (`sqlite+aiosqlite:///:memory:`). Mocks limitados solo a APIs externas remotos.
  - `tests/e2e/`: Pruebas de caja negra con el servidor en marcha, atacando los Endpoints con `httpx.AsyncClient` simulando llamadas WS o CRUD de configuración. Configurado en `tests/conftest.py`. Mocks aplicados a `GroqAdapter` y `AzureAdapter` inyectados en runtime.

- **Frontend (Vitest / React Testing Library)**:
  - `__tests__/components/`: Verificación de renderizado usando mocks del Store.
  - `__tests__/slices/`: Verificación de Mutación de Redux y Thunks fallidos/exitosos consumiendo endpoints falsos (`msw` o `vi.mock()`).
  - `__tests__/simulator/`: Pruebas simuladas de comportamiento bidireccional de WebSocket.

---

### 🧹 7. SCRIPTS & UTILITARIOS
Ruta: `Victoria/scripts/`
Automatizan las tareas tediosas de DevOps para mitigar error humano:
- `check_env.py`: Valida fuertemente que todas las variables en un `.env` dado estén declaradas y no vacías. Falla el subproceso (exit 1) deteniendo el build si falta algo.
- `database/backup.py`: Tarea Cron o manual que realiza copia del archivo SQLite físico con timestamp y poda el histórico (manteniendo top X).
- `maintenance/cleanup.py`: Elimina `Calls` y `Transcripts` más antiguos de un umbral temporal en la DB, para entornos sin alta escalabilidad física de disco.
- `health_check.py`: Prueba proactiva de la API (útil para `docker-compose.yml` `healthcheck` conditions).

---
*Fin del Blueprint.*
