# Guía de Contribución

¡Gracias por contribuir a Victoria!

## Flujo de Trabajo

1.  Hacer fork del repositorio.
2.  Crear una rama para tu feature/fix (`git checkout -b feature/nueva-funcionalidad`).
3.  Implementar cambios.
4.  **Ejecutar Tests**: Asegúrate de que `pytest` pase antes de hacer commit.
5.  Hacer Push y abrir Pull Request.

## Estándares de Testing

*   **Unit Tests**: Obligatorios para toda nueva lógica de negocio o adaptadores. Deben ser rápidos y no depender de servicios externos (usar mocks).
*   **Integration Tests**: Para probar interacción con BD o Redis. Usar `tests/integration/`.
*   **Coverage**: No disminuir el % actual (72%).

## Comandos Útiles

```bash
# Correr linter
ruff check .

# Correr tests rápidos
pytest --ignore=tests/integration

# Generar reporte de coverage
pytest --cov=backend --cov-report=html
```

## Estructura de commits

Usa [Conventional Commits](https://www.conventionalcommits.org/):
*   `feat: ...`
*   `fix: ...`
*   `docs: ...`
*   `refactor: ...`
*   `test: ...`
