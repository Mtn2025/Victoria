# Planos Maestros de Arquitectura - Victoria Voice Orchestrator

Este documento contiene los planos detallados (blueprints) de la arquitectura del sistema Victoria, representados mediante diagramas Mermaid y descripciones estructurales.

## 1. Topología del Sistema (Vista de Alto Nivel)

El sistema Victoria se compone de una interfaz de usuario en React (Frontend) que interactúa con un Backend en Python. El Backend orquesta múltiples servicios de IA y telefonía.

```mermaid
graph TD
    %% Clientes
    Browser["Navegador Web (UI React)"]
    SIP_Client["Cliente SIP / Teléfono"]

    %% Red / Entrada
    API_Gateway["Nginx / Ingress"]

    %% Interfaces Backend
    subgraph "Backend (FastAPI)"
        HTTP_Interface["HTTP API (Config/Historial)"]
        WS_Interface["WebSocket API (Audio Stream)"]
        Webhooks["Webhooks (Telephony)"]
    end

    %% Capa de Aplicación y Dominio
    subgraph "Core (Hexagonal)"
        ApplicationLayer["Application Layer (Orchestrator)"]
        DomainLayer["Domain Layer (Entities & Rules)"]
    end

    %% Infraestructura y Datos
    subgraph "Infraestructura & Datos"
        DB[("Base de Datos (PostgreSQL/SQLite)")]
        Cache[("Redis (PubSub/Cache)")]
        
        %% Adaptadores Externos
        LLM_Adapter["Adaptador LLM (Groq/OpenAI)"]
        TTS_Adapter["Adaptador TTS (Azure/ElevenLabs)"]
        STT_Adapter["Adaptador STT (Azure/Deepgram)"]
        Telephony["Proveedor Telefonía (Twilio/Telnyx)"]
    end

    %% Conexiones
    Browser -- "HTTP(S)" --> API_Gateway
    Browser -- "WSS" --> API_Gateway
    SIP_Client -- "SIP/RTP" --> Telephony
    Telephony -- "Webhooks" --> API_Gateway
    Telephony -- "WSS (Media)" --> API_Gateway

    API_Gateway --> HTTP_Interface
    API_Gateway --> WS_Interface
    API_Gateway --> Webhooks

    HTTP_Interface --> ApplicationLayer
    WS_Interface --> ApplicationLayer
    Webhooks --> ApplicationLayer

    ApplicationLayer <--> DomainLayer

    ApplicationLayer --> DB
    ApplicationLayer --> Cache
    ApplicationLayer --> LLM_Adapter
    ApplicationLayer --> TTS_Adapter
    ApplicationLayer --> STT_Adapter
```

## 2. Arquitectura Hexagonal (Backend Core)

El patrón de Puertos y Adaptadores garantiza que el Dominio (Core) no tenga dependencias de frameworks técnicos.

```mermaid
%%{init: {'theme': 'default'}}%%
graph TD
    subgraph "Interfaces (Primary Adapters)"
        REST["REST Endpoints (FastAPI)"]
        WS["WebSocket Handlers"]
        TelephonyWebhooks["Telephony Webhooks"]
    end

    subgraph "Application (Use Cases & Orchestration)"
        Services["Call Orchestrator"]
        Processors["STT/LLM/TTS Processors pipeline"]
    end

    subgraph "Domain (The Core)"
        Entities["Entities (Call, Agent, Conversation)"]
        ValueObjects["Value Objects (CallId, VoiceConfig)"]
        Ports["Ports (Interfaces para Adapters)"]
    end

    subgraph "Infrastructure (Secondary Adapters)"
        Repo["SqlAlchemy Repositories"]
        LLM_Groq["Groq Adapter"]
        TTS_Azure["Azure TTS Adapter"]
        STT_Azure["Azure STT Adapter"]
    end

    %% Relaciones
    REST -.-> Services
    WS -.-> Services
    TelephonyWebhooks -.-> Services

    Services --> Entities
    Services --> Ports
    Processors --> Ports
    
    Repo -. "Implementa" .-> Ports
    LLM_Groq -. "Implementa" .-> Ports
    TTS_Azure -. "Implementa" .-> Ports
    STT_Azure -. "Implementa" .-> Ports
    
    %% Flujo de Inyección de Dependencias
    Services -. "Inyecta" .-> Repo
    Services -. "Inyecta" .-> LLM_Groq
```

## 3. Modelo de Dominio (Entidades Principales)

Representación conceptual de las entidades y su relación en el dominio.

```mermaid
classDiagram
    class Call {
        +CallId id
        +CallStatus status
        +Agent agent
        +Conversation conversation
        +datetime start_time
        +datetime end_time
        +PhoneNumber phone_number
        +start()
        +end()
    }

    class Agent {
        +str name
        +str system_prompt
        +VoiceConfig voice_config
        +str first_message
    }

    class Conversation {
        +List~ConversationTurn~ turns
        +add_turn(role, content)
        +get_transcript()
    }

    class VoiceConfig {
        <<Value Object>>
        +str name
        +str provider
        +str style
        +float speed
        +float pitch
    }

    class ConversationTurn {
        <<Value Object>>
        +str role
        +str content
        +datetime timestamp
    }

    Call "1" *-- "1" Agent : tiene
    Call "1" *-- "1" Conversation : contiene
    Agent "1" *-- "1" VoiceConfig : usa
    Conversation "1" *-- "many" ConversationTurn : historial
```

## 4. Flujo de Datos Dinámico (Ejemplo: WebSocket Streaming Pipeline)

Este diagrama de secuencia ilustra cómo fluyen los datos de audio a través de los procesadores en una llamada browser-based a través del `CallOrchestrator`.

```mermaid
sequenceDiagram
    actor User as Usuario (Browser)
    participant WS as WebSocket Endpoint
    participant VAD as VAD Processor
    participant STT as Azure STT Adapter
    participant LLM as Groq LLM Adapter
    participant TTS as Azure TTS Adapter
    participant DB as Repository (SQLite/PG)

    User->>WS: Envía Chunk de Audio PCM/G711
    WS->>VAD: Analiza audio para inicio/fin de voz
    
    alt Usuario está hablando
        VAD-->>WS: VAD_ACTIVE
        WS->>STT: Envía chunk continuo
    else Usuario termina de hablar y hace pausa (Silence Timeout)
        VAD-->>WS: VAD_INACTIVE
        STT->>WS: Transcripción Final ("Hola Victoria")
        
        %% Guardar interacción usuario
        WS->>DB: Guarda ConversationTurn (Usuario)
        
        %% Iniciar Generación de Respuesta
        WS->>LLM: Genera Respuesta (Contexto + "Hola Victoria")
        
        %% Streaming LLM a TTS (Pipeline On-The-Fly)
        loop Por cada token/frase (Streaming)
            LLM-->>WS: Chunk de Texto ("¡Hola!")
            WS->>TTS: Sintetiza Chunk de Texto
            TTS-->>WS: Chunk de Audio (Respuesta)
            WS->>User: Envía Chunk de Audio de Respuesta
        end
        
        %% Guardar respuesta asistente
        WS->>DB: Guarda ConversationTurn (Victoria)
    end
```

## 5. Topología de Despliegue (Production Docker Compose)

Arquitectura física de contenedores sugerida para un entorno productivo como un VPS o instancia Cloud.

```mermaid
graph LR
    Internet((Internet))
    
    subgraph "Docker Host (App Server)"
        Proxy[/"Reverse Proxy (Nginx/Traefik)"/]
        
        subgraph "Aplicación"
            Frontend["Victoria Frontend (Nginx/Static)"]
            Backend["Victoria Backend (Uvicorn/Gunicorn)"]
        end
        
        subgraph "Servicios de Soporte"
            DB[("Base de Datos (PostgreSQL)")]
            Redis[("Redis (PubSub/Estado)")]
            Prometheus["Prometheus (Metricas)"]
            Promtail["Promtail (Logs)"]
        end
    end
    
    subgraph "External Cloud Services"
        LLMCloud((Groq / OpenAI API))
        TTSCloud((Azure TTS API))
        TelephonyCloud((Twilio / Telnyx API))
        SentryCloud((Sentry.io))
        LokiCloud((Loki / Grafana Cloud))
    end
    
    Internet -->|HTTPS / WSS| Proxy
    Proxy --> Frontend
    Proxy --> Backend
    
    Backend --> DB
    Backend --> Redis
    
    Backend --> LLMCloud
    Backend --> TTSCloud
    Backend --> TelephonyCloud
    Backend -.-> SentryCloud
    
    Prometheus -. "Scrape /metrics" .-> Backend
    Promtail -. "Lee Docker Logs" .-> Backend
    Promtail -. "Envía Logs" .-> LokiCloud
```
