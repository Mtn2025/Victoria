# Deuda Técnica - Fase 5 (Infrastructure Adapters)

Este documento rastrea la deuda técnica identificada durante la auditoría de Adaptadores de Infraestructura.

## STT (`azure_stt_adapter.py`)

| ID | Tipo | Descripción | Ubicación | Corrección Sugerida | Estado |
|----|------|-------------|-----------|---------------------|--------|
| DT-INFRA-001 | Crítico | Llamada bloqueante en `transcribe` | `AzureSTTAdapter.transcribe` | La llamada `result_future.get()` bloqueaba el Event Loop. Se envolvió en `run_in_executor`. | ✅ Resuelto |
| DT-INFRA-002 | Diseño | Configuración de AudioStream manual | `transcribe` | La creación manual de `PushAudioInputStream` para one-shot es compleja y propensa a errores si no se cierra. | ⚠️ Observación |

## TTS (`azure_tts_adapter.py`)

| ID | Tipo | Descripción | Ubicación | Corrección Sugerida | Estado |
|----|------|-------------|-----------|---------------------|--------|
| DT-INFRA-003 | Rendimiento | Streaming simulado | `synthesize_stream` | Actualmente sintetiza todo el audio y luego lo trocea. Debería usar streaming real de Azure para reducir TTFB. | ⚠️ Alta Prioridad (Fase 9) |
| DT-INFRA-004 | Calidad | Mapeo de Volumen | `_build_ssml` | El mapeo de int (0-100) a SSML volume property necesita validación con la doc de Azure (suele usar %, "medium", etc). | ⚠️ Observación |

## Persistence (`call_repository.py`, `transcript_repository.py`)

| ID | Tipo | Descripción | Ubicación | Corrección Sugerida | Estado |
|----|------|-------------|-----------|---------------------|--------|
| DT-INFRA-005 | Rendimiento | Sincronización de Transcripts por borrado | `CallRepository.save` | Borrar e insertar todos los transcripts de una llamada es ineficiente para llamadas largas. Migrar a `merge` o lógica de append. | ⚠️ Observación |
| DT-INFRA-006 | Datos | Reconstrucción de Agente incompleta | `CallRepository.get_by_id` | Se reconstrute `Agent` desde `CallModel.agent` pero faltan campos (ej. `voice_provider`). Configurar correctamente `AgentModel`. | ⚠️ Observación |
| DT-INFRA-008 | Integridad | Lookup de ID extra | `TranscriptRepository.save` | Requiere una query extra para resolver UUID -> PK Int. Ineficiente bajo carga alta, pero necesario por diseño actual de DB. | ⚠️ Observación |

## LLM (`groq_adapter.py`)

| ID | Tipo | Descripción | Ubicación | Corrección Sugerida | Estado |
|----|------|-------------|-----------|---------------------|--------|
| DT-INFRA-007 | Calidad | Tipado nativo en versión <3.9 | `get_available_models` | Uso de `list[]` corregido a `List[]`. | ✅ Resuelto |

---
