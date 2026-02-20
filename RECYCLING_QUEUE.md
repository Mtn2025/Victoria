# RECYCLED CODE QUEUE

This document stores code snippets from the legacy system that were identified during migration but belong to a different layer or were not immediately applicable.

## [B] Mixed Code - Validation Logics

**ORIGEN:** `/app/schemas/input_validation.py`
**DESTINO SUGERIDO:** `Victoria/backend/interfaces/http/schemas` or `Victoria/backend/infrastructure/validation`

```python
    @field_validator('system_prompt', 'first_message')
    @classmethod
    def sanitize_text_fields(cls, v: str | None) -> str | None:
        """Sanitize text fields to remove potentially dangerous content."""
        if not v:
            return v

        # Remove null bytes
        v = v.replace('\x00', '')

        # Remove script tags and other dangerous HTML
        dangerous_patterns = [
            '<script', '</script>',
            'javascript:',
            'onerror=', 'onload=',
            '<iframe', '</iframe>',
        ]

        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError(f"Input contains dangerous pattern: {pattern}")

        return v.strip()
```

**NOTE:** This sanitization logic is crucial for security but belongs in the Interface/Application layer, not in the pure Domain Value Objects (which should ideally receive already clean data or perform structural validation only).

---
