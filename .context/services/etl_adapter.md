# Service Spec: ETL Adapter (Ampliación)

## 1. Identidad y Red
- **Contenedor:** `prd-api-etl-adapter-fastapi-01`
- **VM:** VM 102 (192.168.0.32)
- **Tecnología:** FastAPI + Python
- **Seguridad:** Solo accesible desde red privada vía API Key interna.

## 2. Responsabilidades y Scope (Estricto)
1. **Ingesta:** Datos externos por cliente (WordPress, CSV, etc.).
2. **Mapeo Multitenant:** Uso de reglas declarativas por cliente para transformar campos heterogéneos (ej: "cacao" -> "property_id").
3. **Validación:** Contra esquema canónico interno.
4. **Hashing (SHA-256):** Sobre contenido normalizado para detectar cambios reales y evitar reprocesamiento.
5. **Upsert:** Persistencia en Postgres (VM 101) en tablas `stage`, `canónicas` y `hashes`.

## 3. Contrato de API (POST /etl/run)
**Input esperado:**
```json
{
  "client_id": "string",
  "source": { "type": "string", "endpoint": "string", "auth_ref": "string" },
  "mapping_id": "string",
  "mode": "upsert"
}