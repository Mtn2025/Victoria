# Auditoría de Migración - FASE 6 (Database & Schemas)

**Fecha:** 19/02/2026
**Auditor:** Agente IA (Antigravity)
**Versión:** 1.0

## 1. Inventario de Schema

Se ha auditado la definición del esquema de base de datos en `backend/infrastructure/database/models/`.

| Modelo | Tabla | Estado | Notas |
|--------|-------|--------|-------|
| `AgentModel` | `agents` | ✅ APROBADO | Incluye `voice_provider` (fase 5 fix) y config JSON. |
| `CallModel` | `calls` | ✅ APROBADO | Relaciones `agent` y `transcripts` correctas (lazy loading configurado en repos). |
| `TranscriptModel` | `transcripts` | ✅ APROBADO | FK correcta a `calls`. |

## 2. Estrategia de Migración (Hallazgo Crítico)

### 2.1 Ausencia de Migraciones de Base
*   **Observación**: El directorio `alembic/versions` contiene 4 revisiones, pero ninguna contiene las sentencias `op.create_table`. La revisión inicial `fdb9b4ef6d6a` está vacía.
*   **Mecanismo Actual**: La aplicación utiliza un enfoque "App-Init" en `backend/interfaces/http/main.py`:
    ```python
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    ```
*   **Impacto**: 
    *   En desarrollo (SQLite): Funciona correctamente.
    *   En producción: **RIESGO**. No permite control granular de cambios ni rollbacks seguros. Alembic no está gestionando la creación de tablas.

## 3. Estado de Deuda Técnica

Se ha registrado la falta de migraciones base como deuda técnica crítica para entornos productivos.

**Documentación Adjunta:**
*   `docs/audit/DEUDA_TECNICA_FASE_6.md`

## 4. Conclusión de Fase 6

El esquema definido en código (`models`) es correcto y coherente con el Dominio. La inicialización de la base de datos funciona para el estado actual del proyecto, aunque la estrategia de migraciones debe formalizarse antes de ir a producción real.

**Recomendación:**
🟢 **BLOQUEADA** pero proceder a **FASE 7** bajo riesgo conocido. 
*   *Nota*: Se recomienda generar una migración "baseline" en `alembic` si se planea usar Postgres en breve.
