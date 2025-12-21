# Misión Activa: Inicialización del Semantic Adapter

## Objetivo
Implementar el núcleo del servicio **Semantic Adapter** para realizar pruebas de generación de embeddings y persistencia vectorial.

## Instrucciones Operativas para la IA
1. **Análisis de Contexto**: Consultar `.context/architecture.md` y `.context/services/semantic_adapter.md`.
2. **Contrato de Datos**: El input debe ser el texto normalizado proveniente del esquema en `config/schemas/canonical_document.json`.
3. **Estilo**: Seguir `.context/conventions.md` (Type Hints, Pydantic, tono directo).

## Tareas Pendientes (Scope Inmediato)
- [x] **app/embedder.py**: Configurar la integración con Gemini (Google Generative AI) para generar vectores.
- [x] **app/chunker.py**: Implementar un split de texto (RecursiveCharacterTextSplitter de LangChain) optimizado para el `body_content`.
- [x] **app/vector_repo.py**: Configurar la estructura de conexión a PostgreSQL + pgvector (Índices HNSW).
- [x] **app/api.py**: Crear endpoint para recibir texto, vectorizar y guardar.

## Restricción de Scope
- No implementar lógica de mapeo o limpieza de datos (pertenece al ETL Adapter).
- No implementar la lógica de RAG final (pertenece al Inference Core).