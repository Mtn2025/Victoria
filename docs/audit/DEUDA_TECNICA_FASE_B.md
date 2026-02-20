# Deuda Técnica - Fase B (Entities)

Este documento rastrea la deuda técnica identificada durante la auditoría de Entidades y su estado de resolución.

## Call (`call.py`)

| ID | Tipo | Descripción | Ubicación | Corrección Sugerida | Estado |
|----|------|-------------|-----------|---------------------|--------|
| DT-ENT-001 | Calidad | Falta de imports de tipado | `Imports` | Importar `Any`, `Dict` de `typing` | ✅ Resuelto |
| DT-ENT-002 | Calidad | Tipado genérico vago | `metadata`, `update_metadata` | Usar `Dict[str, Any]` y `value: Any` | ✅ Resuelto |
| DT-ENT-003 | Lógica | Lógica de transición incompleta | `start()` | Implementar lógica de transición o documentar explícitamente | ✅ Resuelto (Documentado) |

## Agent (`agent.py`)

| ID | Tipo | Descripción | Ubicación | Corrección Sugerida | Estado |
|----|------|-------------|-----------|---------------------|--------|
| DT-ENT-004 | Diseño | Falta validación runtime en init | `__init__` | Considerar `__post_init__` para validar campos obligatorios no vacíos | ✅ Resuelto |

## Conversation (`conversation.py`)

| ID | Tipo | Descripción | Ubicación | Corrección Sugerida | Estado |
|----|------|-------------|-----------|---------------------|--------|
| DT-ENT-005 | Calidad | Falta de imports de tipado | `Imports` | Importar `Dict`, `Any` de `typing` | ✅ Resuelto |
| DT-ENT-006 | Calidad | Tipado de retorno genérico | `get_history_as_dicts` | Usar `List[Dict[str, Any]]` y `-> List[Dict[str, Any]]` | ✅ Resuelto |

---
