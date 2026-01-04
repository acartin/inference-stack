# Manual de Implementación: Gestión de Conocimiento (PDFs)

Este documento detalla la arquitectura, base de datos y flujos necesarios para implementar el módulo de "Base de Conocimiento" en el servidor WWW (Laravel/Filament).

---

## 1. Arquitectura de Datos (Servidor WWW)

Para gestionar los PDFs y su estado de sincronización con la IA, se requiere una tabla dedicada en la base de datos de la aplicación Laravel.

### Tabla Sugerida: `knowledge_documents`

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | `BIGINT (PK)` | ID interno del documento. |
| `client_id` | `UUID` | ID del cliente propietario (Tenant). |
| `filename` | `STRING` | Nombre original del archivo (ej: "Manual_Ventas.pdf"). |
| `storage_path` | `STRING` | Ruta relativa en disco (ej: `documents/{uuid}/manual.pdf`). |
| `content_hash` | `STRING` | SHA-256 del contenido de texto (para control de cambios). |
| `sync_status` | `ENUM` | `PENDING`, `SYNCED`, `FAILED`. |
| `last_synced_at` | `TIMESTAMP` | Fecha de la última sincronización exitosa con la IA. |
| `created_at` | `TIMESTAMP` | Fecha de subida. |

---

## 2. Almacenamiento Físico

Se recomienda una estructura de directorios segregada por cliente para facilitar la limpieza y seguridad.

```bash
/storage/app/documents/
├── [CLIENT_UUID_A]/
│   ├── manual_procesos.pdf
│   └── lista_precios.pdf
├── [CLIENT_UUID_B]/
│   └── reglamento.pdf
```

---

## 3. Flujo de Carga e Ingesta (Paso a Paso)

### Paso 1: Subida (Frontend)
El usuario sube el PDF mediante el formulario de Filament.
*   **Acción**: Guardar archivo en disco y crear registro en `knowledge_documents` con status `PENDING`.

### Paso 2: Extracción de Texto (Backend Job)
Se debe procesar el PDF para extraer el texto plano.
*   **Herramienta recomendada**: `spatie/pdf-to-text` (binario `pdftotext`).
*   **Validación**: Si el texto es < 50 caracteres, marcar como error (posible PDF de imagen escaneada).

### Paso 3: Sincronización con IA (Llama a API)
Enviar el texto extraído al **Semantic Adapter**.

*   **Endpoint**: `POST http://192.168.0.32:8002/api/v1/ingest`
*   **Headers**: `Content-Type: application/json`
*   **Payload**:
    ```json
    {
      "content_id": "knowledge_documents_{id}",  // ID único estable
      "source": "knowledge_base",
      "title": "{filename}",
      "body_content": "{texto_extraido}",
      "hash": "{sha256_del_texto}",
      "metadata": {
        "client_id": "{client_id}",
        "category": "knowledge_base",
        "original_filename": "{filename}"
      }
    }
    ```

### Paso 4: Confirmación
*   **Éxito (200 OK)**: Actualizar `knowledge_documents` -> `status: SYNCED`, `last_synced_at: NOW()`, `content_hash`: `{hash}`.
*   **Fallo**: Marcar `status: FAILED` y guardar mensaje de error.

---

## 4. Flujo de Actualización

Si el usuario reemplaza el archivo PDF:
1.  Se extrae el nuevo texto.
2.  Se calcula el nuevo Hash.
3.  Si el Hash es diferente al guardado en DB, se re-envía al endpoint `/ingest` con el **mismo `content_id`**.
4.  La IA actualizará automáticamente los vectores viejos por los nuevos.

---

## 5. Flujo de Borrado (Protocolo de 3 Capas)

Al eliminar un documento (o un cliente entero), se debe garantizar la limpieza total.

### Caso A: Borrar un solo Documento (Borrador Granular)
Si el usuario elimina un archivo específico pero mantiene el cliente:

1.  **Capa Vectores (API IA)**:
    *   **Endpoint**: `DELETE http://192.168.0.32:8002/api/v1/client/{client_id}/document/{content_id}`
    *   **Acción**: Borra únicamente los vectores asociados a ese documento específico.
2.  **Capa Archivos (Disco)**:
    *   Borrar el archivo físico específico.
3.  **Capa Base de Datos (Laravel)**:
    *   Borrar (o Soft Delete) el registro en `knowledge_documents`.

### Caso B: Borrar Cliente Completo (Baja de Servicio)
**Orden de Ejecución Obligatorio:**

1.  **Capa Vectores (API IA)**:
    *   `DELETE http://192.168.0.32:8002/api/v1/client/{client_id}`
    *   Este paso borra la "memoria" del bot sobre ese cliente.
2.  **Capa Archivos (Disco)**:
    *   `File::deleteDirectory("documents/{client_id}")`
3.  **Capa Base de Datos (Agentic)**:
    *   `DELETE FROM lead_clients WHERE id = {client_id}`
    *   Gracias al `ON DELETE CASCADE`, esto borrará chat, leads y configuración automáticamente.

---

## Resumen de Endpoints (Servidor AI)

| Acción | Método | Endpoint | Payload Clave |
| :--- | :--- | :--- | :--- |
| **Ingestar** | `POST` | `/api/v1/ingest` | `content_id`, `body_content`, `client_id` |
| **Borrar Cliente** | `DELETE` | `/api/v1/client/{id}` | N/A |
| **Salud** | `GET` | `/api/v1/health` | N/A |
