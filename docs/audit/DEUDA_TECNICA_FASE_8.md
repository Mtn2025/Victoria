# Deuda Técnica - Fase 8 (Interfaces)

Este documento rastrea la deuda técnica identificada durante la auditoría de Interfaces.

## Interfaces HTTP (`backend/interfaces/http`)

| ID | Tipo | Descripción | Ubicación | Corrección Sugerida | Estado |
|----|------|-------------|-----------|---------------------|--------|
| DT-INT-001 | Arquitectura | Bypass de UseCase en History | `endpoints/history.py` | Endpoint accede directo a `CallRepository`. Crear `GetCallHistoryUseCase` si se añade lógica de filtrado compleja. | ℹ️ Baja |
| DT-INT-002 | Seguridad | Webhooks sin validación de auth | `endpoints/telephony.py` | Implementar autenticación ligera (X-API-Key / Custom Header) para evitar latencia de validación de firmas criptográficas. | ⚠️ Media |
| DT-INT-003 | Estándar | URL de WebSocket hardcoded | `endpoints/telephony.py` | La URL de retorno (`wss://...`) se construye manualmente. Usar `url_for` o configuración. | ℹ️ Baja |

---
