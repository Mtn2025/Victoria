# Victoria Architecture Guide

## Overview
Victoria follows a **Strict Hexagonal Architecture (Ports & Adapters)** to ensure isolation of business logic, testability, and technology independence.

## 1. Directory Structure & Rules

### `backend/domain` (The Core)
- **Role**: Contains pure business logic, entities, value objects, and ports (interfaces).
- **Dependencies**: ZERO external dependencies. Only Python stdlib.
- **Components**:
  - `Entities`: Mutable business objects with lifecycle (e.g., `Call`, `Agent`).
  - `Value Objects`: Immutable primitives (e.g., `PhoneNumber`, `VoiceConfig`).
  - `Ports`: Abstract interfaces defining how the domain interacts with the world (Structure: `backend/domain/ports/`).
  - `Use Cases`: Application service logic orchestrating entities (Structure: `backend/domain/use_cases/`).

### `backend/application` (The Orchestrator)
- **Role**: Coordinates data flow between Interfaces and Domain.
- **Dependencies**: Can import Domain and Infrastructure adapters.
- **Components**:
  - `Services`: Complex coordination logic (e.g., `CallOrchestrator`).
  - `Processors`: Stateless transformation pipelines (e.g., `LLMProcessor`).

### `backend/infrastructure` (The Adapters)
- **Role**: Implements Domain Ports using specific technologies.
- **Dependencies**: External libraries (SQLAlchemy, Twilio SDK, Azure SDK).
- **Components**:
  - `Adapters`: Concrete implementations of Ports (e.g., `TwilioAdapter`, `SqlAlchemyRepository`).
  - `Database`: ORM models and session management.
  - `Config`: Environment settings.

### `backend/interfaces` (The Entry Points)
- **Role**: Handles external input/output.
- **Dependencies**: Web frameworks (FastAPI).
- **Components**:
  - `HTTP`: REST endpoints.
  - `WebSocket`: Real-time audio streams.

## 2. Dependency Rule
**Dependencies must point INWARDS.**
`Interfaces` -> `Application` -> `Domain` <- `Infrastructure`

- Domain knows NOTHING about unnecessary details (DB, API).
- Infrastructure depends on Domain (to implement Ports).
- Application orchestrates both.

## 3. Data Flow Example: Inbound Call
1. **Interface**: `HTTP POST /webhook/telephony` receives request.
2. **Interface**: Validates payload -> Converts to DTO.
3. **Application**: Calls `StartCallUseCase` (in `application/services` or `domain/use_cases`).
4. **Domain**: `Call` Entity is created.
5. **Infrastructure**: `SqlAlchemyCallRepository` saves state to SQLite.
6. **Infrastructure**: `TelephonyAdapter` answers the call via Twilio API.
