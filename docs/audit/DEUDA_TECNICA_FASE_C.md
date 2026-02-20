# Deuda Técnica - Fase C (Domain Ports)

Este documento rastrea la deuda técnica identificada durante la auditoría de Puertos del Dominio y su estado de resolución.

## Repositories (`persistence_port.py`, `transcript_repository_port.py`, `config_repository_port.py`)

| ID | Tipo | Descripción | Ubicación | Corrección Sugerida | Estado |
|----|------|-------------|-----------|---------------------|--------|
| DT-PORT-001 | Crítico | Desajuste de tipo en ID | `TranscriptRepositoryPort.save` | Cambiar `call_id: int` a `call_id: str` (o `CallId`) | ✅ Resuelto |
| DT-PORT-002 | Calidad | Tipado Union moderno (3.10+) en proyecto 3.9+ | `ConfigDTO`, `ConfigRepositoryPort` | Cambiar `T | None` a `Optional[T]` | ✅ Resuelto |
| DT-PORT-003 | Calidad | Falta de tipado en `**kwargs` | `ConfigRepositoryPort.update_config` | Explicitar `**updates` o usar `Dict[str, Any]` | ⚠️ Observación (Mantener flexible) |

## AI Services (`llm_port.py`, `stt_port.py`, `tts_port.py`)

| ID | Tipo | Descripción | Ubicación | Corrección Sugerida | Estado |
|----|------|-------------|-----------|---------------------|--------|
| DT-PORT-004 | Consistencia | Uso de genéricos built-in (`list`) vs `typing.List` | `STTConfig.keywords`, `tool_models.py` | Estandarizar a `List`, `Dict` | ✅ Resuelto |
| DT-PORT-005 | Consistencia | Parámetro `format` como string | `TTSRequest` | Usar Value Object `AudioFormat` o validación explícita | ⚠️ Observación |
| DT-PORT-006 | Calidad | Tipado débil en `on_interruption_callback` | `STTPort.start_stream` | Usar `Callable[[], None]` o similar | ⚠️ Observación |

## Infrastructure Support (`cache_port.py`, `tool_port.py`)

| ID | Tipo | Descripción | Ubicación | Corrección Sugerida | Estado |
|----|------|-------------|-----------|---------------------|--------|
| DT-PORT-007 | Calidad | Falta de retorno `-> None` | `CachePort` methods | Añadir `-> None` explícito | ✅ Resuelto |
| DT-PORT-008 | Calidad | Tipado Union moderno | `CachePort.get` | Cambiar `Any | None` a `Optional[Any]` | ✅ Resuelto |

---
