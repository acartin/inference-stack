# Convenciones de Desarrollo

- **Estilo de Código**: Python 3.11+, tipado estricto con Type Hints.
- **Validación**: Uso obligatorio de Pydantic para todos los modelos de datos.
- **Interacción con la IA**: 
    - No usar frases de adulación o relleno ("excelente pregunta", etc).
    - Ir directo a la solución técnica.
- **Documentación**: Comentarios breves y funcionales en el código.

## Manejo de Datos
- **Esquema Canónico**: Toda comunicación de datos normalizados DEBE seguir estrictamente `config/schemas/canonical_document.json`.
- **Extensibilidad**: Información adicional específica de la fuente que no quepa en los campos raíz debe ir dentro del objeto `metadata`.