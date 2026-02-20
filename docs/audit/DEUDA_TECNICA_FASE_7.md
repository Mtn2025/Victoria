# Deuda Técnica - Fase 7 (Application Services)

Este documento rastrea la deuda técnica identificada durante la auditoría de Servicios de Aplicación.

## Arquitectura (`backend/application/`)

| ID | Tipo | Descripción | Ubicación | Corrección Sugerida | Estado |
|----|------|-------------|-----------|---------------------|--------|
| DT-APP-001 | Arquitectura | Lógica de Negocio en Controlador HTTP | `endpoints/config.py` | La lógica de actualización de agente debe moverse a `UpdateAgentConfigUseCase` en capa de Aplicación. | ⚠️ Media |
| DT-APP-002 | Arquitectura | Acoplamiento Infra-Interfaz | `endpoints/config.py` | El endpoint instancia `AzureTTSAdapter` directamente. Usar `GetVoiceOptionsUseCase` con inyección de dependencia. | ⚠️ Media |
| DT-APP-003 | Calidad | Hack de Proxy en VAD | `vad_processor.py` | `VADProcessor` crea una clase fake `ConfigAgent` para satisfacer la firma de `DetectTurnEndUseCase`. Refactorizar UseCase para aceptar config simple o pasar Agent real. | ℹ️ Baja |
| DT-APP-004 | Hardcoding | Modelo LLM default | `llm_processor.py` | Modelo `llama-3.3-70b-versatile` hardcoded como fallback. Mover a configuración centralizada. | ℹ️ Baja |

---
