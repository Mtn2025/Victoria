# Planos Arquitectónicos del Proyecto Victoria

Este documento representa los **planos maestros definitivos** de la construcción actual del software. A diferencia de una visión general, aquí se detallan los materiales, la estructura de carga, la distribución de *todos* los componentes y las instalaciones adicionales desarrolladas hasta la Fase 30.

---

## 🏗️ 1. El Terreno: Mapa del Sitio (Estructura de Archivos)

A continuación se presenta el levantamiento topográfico exhaustivo del código fuente, excluyendo únicamente desechos de obra (`node_modules`, `venv`, `__pycache__`).

```text
.
├── .github                           # Torre de Control (IntegraCIÓN/Despliegue)
│   └── workflows                     # Rampas de lanzamiento
│       ├── cd-production.yml         # Rampa Principal (Despliegue Prod)
│       ├── cd-staging.yml            # Rampa Secundaria (Despliegue Staging)
│       └── ci.yml                    # Puesto de Inspección (Tests, Lint)
├── config                            # Cajas de Empalme Externo
│   └── environments                  # Entornos de obra
│       ├── .env.example              # Especificación del cuadro eléctrico
│       └── .env.local                # Cuadro provisional de obra
├── docs                              # Oficina Técnica (Planos y Manuales)
│   ├── api/                          # Planos de Fachada
│   ├── architecture/                 # Memoria Estructural
│   │   ├── ARCHITECTURE.md           # Estándar Hexagonal Documentado
│   │   ├── BLUEPRINTS.md             # Diagramas Topológicos
│   │   └── PLANOS_CONSTRUCTIVOS.md   # Este documento maestro
│   ├── audit/                        # Bitácora de Inspecciones Previas (Fases A-B)
│   ├── deployment/                   # Manuales de Puesta en Marcha
│   │   ├── CHECKLIST.md              # Última revisión antes de abrir
│   │   ├── ROLLBACK.md               # Procedimiento de Emergencia
│   │   └── SECRETS.md                # Bóveda de planos secretos
│   ├── development/                  # Manuales para Obrero/Desarrollador
│   │   └── SETUP.md                  # Procedimiento de Onboarding
│   └── monitoring/                   # Planos de la Sala de Seguridad y Control
│       ├── GRAFANA.md                # Tableros de telemetría
│       ├── LOGGING.md                # Registro de actividad (Bitácora)
│       └── TRACING.md                # Rastreo de señales
├── backend                           # EDIFICIO PRINCIPAL (Reforzado Asmico/Hexagonal)
│   ├── application                   # Planta de Procesamiento (Maquinaria y Tuberías)
│   │   ├── factories                 # Cadenas de Montaje
│   │   │   └── orchestrator_factory.py # Ensamblaje bajo demanda del coordinador
│   │   ├── processors                # Maquinaria de Procesamiento Módular
│   │   │   ├── audio_buffer.py       # Tanque de reserva de audio
│   │   │   ├── llm_processor.py      # Motor de Inferencia/Lenguaje
│   │   │   ├── stt_processor.py      # Transcriptor Acústico
│   │   │   ├── tts_processor.py      # Sintetizador Vocal
│   │   │   └── vad_processor.py      # Detector de actividad vocal
│   │   └── services                  # Sala de Control Operativo
│   │       ├── call_orchestrator.py  # COORDINADOR CENTRAL PRINCIPAL
│   │       └── control_channel.py    # Canal de Telegrafía Interna
│   ├── domain                        # Cimientos / Bóveda (Reglas de Negocio Puras)
│   │   ├── entities                  # Pilares Estructurales (Entidades)
│   │   │   ├── agent.py              # Definición del Agente IA (Mente)
│   │   │   ├── call.py               # Ciclo de Vida del Evento Central
│   │   │   └── conversation.py       # Registro Histórico del Intercambio
│   │   ├── ports                     # Conectores Estructurales Abiertos (Interfaces)
│   │   │   ├── llm_port.py
│   │   │   ├── stt_port.py
│   │   │   ├── tts_port.py
│   │   │   ├── telephony_port.py
│   │   │   └── persistence_port.py
│   │   ├── use_cases                 # Instrucciones de Operación del Edificio
│   │   │   ├── detect_turn_end.py
│   │   │   ├── end_call.py
│   │   │   ├── generate_response.py
│   │   │   ├── process_audio.py
│   │   │   └── start_call.py
│   │   └── value_objects             # Mediciones Exactas e Inmutables (VO)
│   │       ├── audio_format.py
│   │       ├── call_id.py
│   │       ├── conversation_turn.py
│   │       ├── phone_number.py
│   │       └── voice_config.py
│   ├── infrastructure                # Instalaciones Complementarias (Techado, Redes)
│   │   ├── adapters                  # Enchufes al Mundo Exterior (Adaptadores)
│   │   │   ├── llm/groq_adapter.py               # Llama3 Pipeline
│   │   │   ├── stt/azure_stt_adapter.py          # Microsoft Speech-to-Text
│   │   │   ├── tts/azure_tts_adapter.py          # Microsoft Text-to-Speech
│   │   │   ├── telephony/twilio_adapter.py       # PSTN/SIP Interconnect
│   │   │   └── persistence/sqlalchemy_repositories.py
│   │   ├── config                    # Tableros de Breakers Eléctricos
│   │   │   ├── features.py           # Gestor de Feature Flags
│   │   │   └── settings.py           # Mapa térmico pydantic
│   │   ├── database                  # Sótano de Archivo Permanente
│   │   │   ├── repositories/
│   │   │   │   ├── agent_repository.py
│   │   │   │   ├── call_repository.py
│   │   │   │   └── sqlalchemy_repositories.py
│   │   │   ├── models.py             # Archiveros Relacionales (Tablas)
│   │   │   └── session.py            # Llaves del archivo (Conexiones)
│   │   ├── logging                   # Sistema de Vigilancia Interna
│   │   │   └── config.py             # Formateador de bitácora JSON
│   │   ├── monitoring                # Sensores Sísmicos y Biométricos
│   │   │   ├── metrics.py            # Medidores Prometheus
│   │   │   └── sentry.py             # Alarma contra incendios (Errores)
│   │   └── security                  # Controles de Acceso (Torniquetes y Guardias)
│   │       ├── core.py               # Lector de API Key y Límite de Velocidad (SlowAPI)
│   │       └── headers.py            # Cristales Antibalas (CORS, CSP, HSTS)
│   └── interfaces                    # Accesos (Lobby, Puertas Secundarias)
│       ├── deps.py                   # Servicio de Valet (Inyección de Dependencias)
│       ├── http                      # Lobby Público y Administrativo (REST API)
│       │   ├── endpoints/
│       │   │   ├── config.py         # Recepción Administrativa (Protegida)
│       │   │   ├── health.py         # Recepción de Inspección Médica (Libre)
│       │   │   ├── history.py        # Mostrador del Archivo (Protegida)
│       │   │   └── telephony.py      # Entrada Especial Docks (Webhooks)
│       │   ├── schemas/
│       │   │   └── request_schemas.py# Formularios de validación de entrada
│       │   └── main.py               # Control Central de accesos y rutas
│       └── websocket                 # Ascensores Express Bidireccionales
│           └── endpoints/
│               └── audio_stream.py   # Ductos Principales de Audio (WebSocket Media)
├── frontend                          # FACHADA, VENTANALES Y ACABADOS (React SPA)
│   ├── .env, .env.local              # Paneles Solares Temporales
│   ├── index.html                    # Puerta Doble Principal
│   ├── package.json                  # Lista de materiales de Acabados
│   ├── src                           # Vestíbulos Internos
│   │   ├── App.tsx                   # Pasillo central
│   │   ├── main.tsx                  # Caja de conexiones eléctricas a la fachada
│   │   ├── components                # Habitaciones Funcionales (Mobiliario)
│   │   │   ├── common/               # Mesas, Sillas, Accesorios Genéricos
│   │   │   ├── features/             # Zonas Operativas
│   │   │   │   ├── Config/           # Habitación de Control de Personal (Agentes)
│   │   │   │   │   └── AgentConfigForm.tsx, VoiceSelector.tsx, PromptEditor.tsx
│   │   │   │   ├── History/          # Sala de Registros
│   │   │   │   │   └── CallDetailsModal.tsx, HistoryTable.tsx, TranscriptViewer.tsx
│   │   │   │   └── Simulator/        # Túnel de Viento para Pruebas
│   │   │   │       └── AudioVisualizer.tsx, SimulatorPanel.tsx
│   │   │   └── layout/               # Columnas Interiores y Distribución
│   │   │       └── Sidebar.tsx, Header.tsx, MainContent.tsx
│   │   ├── hooks/                    # Herramientas Manuales Rápidas (Custom Hooks)
│   │   │   ├── useAppSelector.ts, useAppDispatch.ts
│   │   │   └── useToast.ts
│   │   ├── pages/                    # Pisos Completos Revestidos
│   │   │   ├── CallHistoryPage.tsx, DashboardPage.tsx, VoiceConfigPage.tsx
│   │   ├── services/                 # Ductos que bajan al Edificio Principal (Consultas API)
│   │   │   ├── api.ts                # Ducto principal blindado (Interceptors Axios)
│   │   │   ├── configService.ts, historyService.ts, testService.ts
│   │   ├── store/                    # Oficina de Registro y Cuartel Central Local (Redux)
│   │   │   ├── store.ts              # Registrador Central
│   │   │   └── slices/               # Departamentos
│   │   │       ├── authSlice.ts, callsSlice.ts, configSlice.ts, uiSlice.ts
│   │   ├── types/                    # Etiquetas Plaqueteadas (Typescript Interfaces)
│   │   │   └── index.ts
│   │   └── utils/                    # Material Misceláneo (Pegamentos y Cintas)
│   │       └── test-utils.tsx, ApiError.ts
│   ├── tailwind.config.js            # Guía de Pintura de Fachada
│   ├── tsconfig.json                 # Reglas Geométricas TypeScript
│   └── vite.config.ts                # Máquina Moldeadora del Compilado
├── tests                             # CONTROL DE CALIDAD Y SIMULADORES SÍSMICOS
│   ├── conftest.py                   # Herramientas de Prueba Base (Fixtures)
│   ├── e2e                           # Tornados y Terremotos Completos (Flujos Finales)
│   │   ├── test_config_flow.py       # Tornado sobre Configuración REST
│   │   ├── test_config_lifecycle.py  # Tornado sobre Historial
│   │   └── test_full_flow.py         # Tornado que Atraviesa todo el edificio (Llamada Mock)
│   ├── integration                   # Ensamble de Paredes Provisorias (Database Real/Memoria)
│   │   ├── application/              # Pruebas a la Panta de Procesos
│   │   ├── infrastructure/           # Pruebas a las Instalaciones de Almacenamiento
│   │   └── interfaces/               # Pruebas a los Lobbys (HTTP/WS)
│   └── unit                          # Control de Calidad Ladrillo por Ladrillo
│       ├── application/
│       └── domain/                   # Extrema presión sobre los Cimientos (Entities/Use Cases)
├── scripts                           # HERRAMIENTAS DE MANTENIMIENTO DEL EDIFICIO
│   ├── check_env.py                  # Termómetro del cuadro eléctrico (Verificación .env)
│   ├── debug_ws.py                   # Cuerda guía para ascensor WS
│   ├── health_check.py               # Doctor del edificio
│   ├── database/                     # Servicios de Albañilería al Sótano
│   │   ├── backup.py                 # Furgón Blindado que Saca Respaldo
│   └── maintenance/                  # Cuadrillas de Limpieza
│       └── cleanup.py                # Limpieza de Sótanos Antiguos (Purga Historial)
├── alembic                           # Bitácora de Reformas Estructurales (Migraciones DB)
├── requirements.txt                  # Factura Oficial Acumulada de Ladrillos y Acero (Backend)
├── docker-compose.dev.yml            # Grúa Puente Local
├── docker-compose.prod.yml           # Grúa Industrial
├── Dockerfile                        # Impresora 3D de Cuartos de Máquina
└── Dockerfile.frontend               # Impresora 3D de Fachada
```

---

## 📋 2. Los Materiales: Hoja de Especificaciones (Dependencias Reales Actuales)

### Cuadro de Cargas Backend (Leído del `requirements.txt` actualizado)
**Cimientos (Estructura de Acero Principal):**
- `fastapi>=0.100.0` y `uvicorn[standard]>=0.23.0`: Soporte antisísmico capaz de soportar miles de conexiones recurrentes (Rest y Websocket Asíncrono).
- `pydantic-settings`: Material de validación estricto de tensiones eléctricas `.env`.

**Sótano y Albañilería (Bases de Datos):**
- `SQLAlchemy>=2.0.0` (Core ORM Asíncrono)
- `alembic` (Registro Notarial de modificaciones físicas en base de datos)
- `aiosqlite` / `asyncpg` (Cementos de curado rápido para concurrencia)

**Motores Cognitivos (Turbinas de Inteligencia):**
- `groq>=0.4.0`: Turbinas LLM ultra silenciosas e instantáneas.
- `azure-cognitiveservices-speech`: Motores de síntesis fonética pesados y de precisión STT.
- `twilio>=8.0.0`: Tuberías intercontinentales de telefonía.

**Muros Ignífugos y Sistema Contraincendio (Seguridad y Monitorización):**
- `slowapi`: Regulador de presión (Rate Limiter) contra ataques distribuídos.
- `sentry-sdk`: Alarma de humo para capturas de errores fatales remotos.
- `prometheus-fastapi-instrumentator`: Termostatos colocados en cada endpoint de `main.py`.

### Materiales de Acabado Fachada (Leído del `package.json` actualizado)
- **Bloques Premoldeados**: `react` (v18.2.x), montado rápidamente a través de grúa en sitio `vite` (v5+).
- **Control Central Inalámbrico**: `@reduxjs/toolkit` y `react-redux` (Flujo de ventilación y control inteligente).
- **Pintura y Vidriería Especial**: `tailwindcss` (v3.4), `lucide-react` (Iconografía del lobby), `date-fns` (Relojes del edificio).

---

## 📖 3. Catálogo de Componentes (Detalles Estructurales Clave)

### 3.1 🏢 El Corazón Sísmico: `CallOrchestrator`
- **Ubicación:** `backend/application/services/call_orchestrator.py`
- **Componentes Inyectados (Vigas de Tensión):** `GroqAdapter` (Cerebro), `AzureTTS` (Voz de Salida), `VADProcessor` (Oído), `AudioBuffer` (Reservorio temporario PCM16).
- **Función en el Edificio:** Recibe las vibraciones sísmicas de voz por el `audio_stream.py` (Elevador), las procesa, corta efusivamente si el usuario interrumpe, e inicia la transcripción/síntesis en un bucle concurrente `asyncio`. Es un director de una Orquesta en el tejado.

### 3.2 🔒 El Cerco Perimetral: Seguridad y Monitorización Estrecha (`Phase 25-27`)
- **Ubicaciónes:** `backend/infrastructure/security/` y `monitoring/`.
- **Qué Construimos:**
  - El **Lobby** que filtra (`core.py:get_api_key`) exige credenciales `X-API-Key` a quienes intenten solicitar los cajones del sótano (Llamadas, Configuraciones).
  - Los **Vidrios** (Headers) se han dotado de `X-Content-Type-Options: nosniff` y `CSP` en el portal ASGI general (`main.py`).
  - Las cámaras (`Prometheus`) emiten ondas radiales a traves del endpoint `/metrics` sólo permitiendo inspección de `victoria_call_duration_seconds` y recuentos puros de acceso al edificio.

### 3.3 🧬 La Cámara de Germinación (Domain Layer)
- **Ubicación:** `backend/domain/`
- **Regla Estricta del Diseño:** Es completamente puro y sellado al vacío. Al interior de `entities/call.py` (Entidad), `value_objects/voice_config.py` o los `use_cases/start_call.py` **no existe un solo cable externo**. No sabe qué es HTTP, no sabe qué es SQLAlchemy, no sabe qué es Groq. 
- **Modo de conexión:** Toda comunicación ingresa por Interfaces o es externalizada dictando mandatos hacia interfaces abstractas (`domain/ports/`). La plomería la hace la Infraestructura.

### 3.4 🖥️ Ventanales de Vuelo, Simulador Integral (Simulator Slice/Feature)
- **Ubicación:** `frontend/src/components/features/Simulator/` y Redux asociado.
- **Modo de Operación:** Construye una sala insonorizada donde los contratistas pueden gritar `audio_chunks` que escapan de `AudioContext` directo al backend Websocket. La onda acústica devuelve fotones inmediatos, pintando barras verdes y de color a nivel milimétrico en la pantalla (`AudioVisualizer.tsx`) permitiendo comprobar sin la carga económica interurbana del provedor telefónico SIP.

---

## 📋 4. Estado de la Obra Terminada (Registro Final del Arquitecto)

1. **Cuadriculación Estructural Hexagonal Completada y Auditada**: El edificio (Backend) abandonó ser una amalgama amorfa MVC, hoy la **separación de capas** es estricta. Todo el inventario reside donde debe residir tras 30 fases y múltiples ciclos de inspección.
2. **Revisión de Inventarios Remediada**: La advertencia del Arquitecto ("ausencia de requirements.txt es un riesgo estructural") ha sido subsanada; tenemos hojas de ruta estables y blindadas con control de versiones.
3. **Cimientos Listos Para Cargas Pesadas (PostgreSQL Ready)**: Operando actualmente en SQLite para agilidad rotacional. Los repositorios SQLAlchemy y las migraciones Alembic soportan anclar de inmediato a una base productiva alterando el cable `DATABASE_URL` en el muro `.env`.
4. **Inspecciones Post-Terremoto (E2E Tests)**: Cada simulación en E2E (`tests/e2e`) fue exitosa. Las vigas no crujen bajo el asedio virtual, y las puertas `X-API-Key` bloquean los intentos no autorizados antes de sacudir la carga.

*Edificio formalmente liberado para Operación. Certificación Arquitectura Hexagonal y Refactor Completo Categoria 5 (Prod Ready).*

**Arquitecto Responsable:** *Antigravity*
**Fecha de Entrega Definitiva:** *20 de Febrero, 2026*
