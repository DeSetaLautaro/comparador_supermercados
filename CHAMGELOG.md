# Registro de Cambios (Changelog)

## [0.1.1] - 2026-06-11
### Corregido
- **Limpieza de IDs:** Se añadió la función `limpiar_ids` para convertir correctamente los IDs de producto de formato float (`1.0`) a string (`1`). Esto evita errores de inconsistencia al realizar cruces de tablas.
- **Integración:** Se refactorizaron las funciones de carga para aplicar esta limpieza antes de insertar en DuckDB.

### Notas
- Cambio sugerido mediante revisión de código con IA.