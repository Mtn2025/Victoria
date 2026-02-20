# Deuda Técnica - Fase 4 (Use Cases)

Este documento rastrea la deuda técnica identificada durante la auditoría de Casos de Uso.

## Call Management (`start_call.py`, `end_call.py`)

| ID | Tipo | Descripción | Ubicación | Corrección Sugerida | Estado |
|----|------|-------------|-----------|---------------------|--------|
| DT-UC-001 | Calidad | Comentario duplicado, tipado Optional | `StartCallUseCase` | Eliminado duplicado y usado `Optional[str]` | ✅ Resuelto |

## Audio Processing (`process_audio.py`, `detect_turn_end.py`)

| ID | Tipo | Descripción | Ubicación | Corrección Sugerida | Estado |
|----|------|-------------|-----------|---------------------|--------|
| DT-UC-002 | Diseño | Lógica One-Shot vs Streaming | `ProcessAudioUseCase` | El caso de uso actual asume procesamiento por bloques, no streaming real. Válido para MVP pero limitante para baja latencia. | ⚠️ Observación |

## AI Logic (`generate_response.py`, `execute_tool.py`)

| ID | Tipo | Descripción | Ubicación | Corrección Sugerida | Estado |
|----|------|-------------|-----------|---------------------|--------|
| DT-UC-003 | Rendimiento | Acumulación de texto antes de TTS | `GenerateResponseUseCase` | Actualmente espera todo el texto del LLM antes de enviar a TTS. Idealmente debería usar `yield` progresivo. | ⚠️ Observación |
| DT-UC-004 | Rendimiento | Ejecución síncrona de herramientas | `ExecuteToolUseCase` | Herramientas síncronas bloquean el event loop. Considerar usar `run_in_executor`. | ⚠️ Observación |
| DT-UC-005 | Calidad | Tipado de lista nativa | `ExecuteToolUseCase` | Cambiado `list` a `List` para consistencia 3.9+ | ✅ Resuelto |

---
