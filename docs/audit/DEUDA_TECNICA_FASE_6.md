# Deuda Técnica - Fase 6 (Database & Schemas)

Este documento rastrea la deuda técnica identificada durante la auditoría de Base de Datos.

## Migrations (`alembic/`)

| ID | Tipo | Descripción | Ubicación | Corrección Sugerida | Estado |
|----|------|-------------|-----------|---------------------|--------|
| DT-DB-001 | Crítico | Falta de Migración Base | `versions/` | Las tablas se crean via `main.py` (`create_all`). Alembic no tiene historia de creación. | ⚠️ Alta Prioridad (Prod) |
| DT-DB-002 | Mantenimiento | Estructura de Directorios | `alembic.ini` | `alembic.ini` en root apunta a `alembic/`, pero la estructura en infraestructura sugiere `infrastructure/database`. Consolidar. | ℹ️ Observación |

## Models (`models/`)

| ID | Tipo | Descripción | Ubicación | Corrección Sugerida | Estado |
|----|------|-------------|-----------|---------------------|--------|
| DT-DB-003 | Rendimiento | Índices redundantes? | `CallModel` | Se han añadido índices en migraciones (`423b...`) que ya estaban en definición de modelo o viceversa. Verificar duplicidad. | ℹ️ Observación |

---
