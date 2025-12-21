# Arquitectura del Sistema: Inference Stack

## 1. Infraestructura y Red
Todos los servicios operan bajo **FastAPI + Python** en contenedores Docker dentro de la **VM 102 (192.168.0.32)**.

| Servicio | Nombre del Contenedor | Dominio Interno |
| :--- | :--- | :--- |
| **ETL Adapter** | `prd-api-etl-adapter-fastapi-01` | Api |
| **Semantic Adapter** | `prd-api-semantic-adapter-fastapi-01` | api |
| **Inference Core** | `prd-api-inference-core-fastapi-01` | api |

## 2. Definición de Servicios (Scope Estricto)

### [ETL Adapter](./services/etl_adapter.md)
* **Rol**: Ingesta y normalización multitenant.
* **Responsabilidades**: Ingesta desde fuentes externas (n8n/POST), normalización canónica, mapeo, validación estructural, hashing de contenido y upsert en tablas (stage/canónicas/hashes).
* **Restricciones**: No realiza inferencia, embeddings, lógica LLM ni orquestación.

### [Semantic Adapter](./services/semantic_adapter.md)
* **Rol**: Inteligencia de datos y persistencia vectorial.
* **Responsabilidades**: Generación de embeddings (OpenAI/Gemini/Local), gestión de PostgreSQL+pgvector (índices HNSW), control de idempotencia mediante hashes únicos y ejecución de búsqueda semántica para el Inference Core.
* **Restricciones**: No realiza ingesta de datos crudos, mapeos estructurales ni inferencia directa con el usuario.

### [Inference Core](./services/inference_core.md)
* **Rol**: Motor central de inferencia y RAG.
* **Responsabilidades**: Recibir consultas normalizadas, resolución de intención (router de agentes), consulta a vector store (pgvector) y bases relacionales, ejecución de lógica de negocio y entrega de respuestas estructuradas contractuales.
* **Restricciones**: No realiza ETL, scraping, parsing de WordPress ni generación de embeddings en batch.

## 3. Flujo de Datos Maestro
1. **Ingesta**: Orígenes externos (como n8n) envían datos al **ETL Adapter** proporcionando `client_id`, `source_type` y `mapping_id`.
2. **Normalización**: El **ETL Adapter** valida contra esquemas canónicos y persiste la metadata de hashes para evitar duplicidad.
3. **Indexación**: Los datos normalizados pasan al **Semantic Adapter** para chunking y generación de embeddings.
4. **Almacenamiento**: El **Semantic Adapter** persiste los vectores en pgvector usando índices HNSW para búsqueda eficiente.
5. **Inferencia**: El **Inference Core** recibe una consulta, solicita el contexto relevante al **Semantic Adapter** y produce una respuesta para canales finales (Web, WhatsApp, etc.).

## 4. Contratos Globales
* **Comunicación**: Interfaz REST vía API para todos los servicios.
* **Idempotencia**: Garantizada por el sistema de hashes únicos en el Semantic Adapter y el hashing de contenido en el ETL Adapter.