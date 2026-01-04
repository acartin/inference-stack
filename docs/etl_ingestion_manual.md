# Manual de Implementación: ETL de Propiedades (Carga Masiva)

Este documento define la arquitectura y lógica para el proceso nocturno de sincronización del catálogo de propiedades entre el servidor WWW (Realtors) y el Inference Stack.

---

## 1. Estrategia de Eficiencia (Local Diff)

**CRÍTICO:** A diferencia de los PDFs manuales, el catálogo puede tener miles de propiedades.
*   **Problema**: Si envías todas las propiedades cada noche a la API `/ingest`, el sistema generará embeddings para todas, **incurriendo en costos altos de API (Gemini)** y uso de CPU, aunque el dato no haya cambiado.
*   **Solución**: El servidor WWW debe actuar como **Filtro Inteligente**. Solo debe enviar a la IA las propiedades que realmente han cambiado (precio, descripción) o son nuevas.

---

## 2. Arquitectura de Datos (Servidor WWW)

Se requiere añadir campos de control a la tabla de propiedades existente en Laravel.

### Tabla: `properties` (Existente)

| Columna | Acción Requerida | Descripción |
| :--- | :--- | :--- |
| `id` | - | ID primario del inmueble. |
| ... | - | Campos de negocio... |
| **`semantic_hash`** | **[NUEVA]** | El último SHA-256 confirmado como sincronizado con la IA. |
| **`semantic_synced_at`** | **[NUEVA]** | Fecha de la última carga exitosa. |

---

## 3. Lógica del Script ETL (Cron Job Nocturno)

El script (ej: `php artisan properties:sync-semantic`) debe seguir este diagrama de flujo para cada propiedad:

1.  **Generación de Data**: Construir el string narrativo que leerá la IA.
    *   *Ejemplo*: "Casa en Venta en Tulum, $250,000 USD. 3 Recámaras, 2 Baños. Amenidades: Alberca, Gym..."
2.  **Cálculo de Hash**: Generar el `SHA-256` de ese string narrativo.
3.  **Comparación Local (The Gatekeeper)**:
    *   `IF (property.semantic_hash == new_hash)`:
        *   **SKIP**: No hacer nada. La IA ya tiene la versión más actual. (Ahorro: 100%).
    *   `ELSE`:
        *   **SEND**: La propiedad cambió (o es nueva). Proceder a llamar a la API.

---

## 4. Interacción con API de Ingesta

Para los registros que pasaron el filtro, enviar al endpoint estándar.

*   **Endpoint**: `POST http://192.168.0.32:8002/api/v1/ingest`
*   **Payload**:
    ```json
    {
      "content_id": "property_{id}",       // Prefijo para evitar colisión con PDFs
      "source": "property_catalog",
      "title": "Casa en {ubicacion} - {codigo}",
      "body_content": "{texto_narrativo}",
      "hash": "{new_hash}",
      "metadata": {
        "client_id": "{client_id}",
        "category": "property_catalog",
        "price": 250000,
        "currency": "USD",
        "location": "Tulum",
        "type": "sale"
      }
    }
    ```

*   **Post-Proceso (Solo si API responde 200 OK)**:
    *   Actualizar en BD Local: `semantic_hash = {new_hash}`, `semantic_synced_at = NOW()`.

---

## 5. Manejo de Propiedades Eliminadas (Bajas)

Si una propiedad se vende o se baja del inventario en el WWW:
1.  El script ETL debe detectar registros que ya no existen (o marcados como `sold`).
2.  **Acción**: Llamar al endpoint de borrado granular.
    *   `DELETE /api/v1/client/{client_id}/document/property_{id}`
3.  **Resultado**: La IA deja de recomendar esa casa inmediatamente.

---

## Resumen de Ahorros

| Escenario | Sin Local Diff | Con Local Diff |
| :--- | :--- | :--- |
| Catálogo de 1,000 casas (Sin cambios) | 1,000 Embeddings (Pago $$) | **0 Embeddings ($0)** |
| 10 casas cambian precio | 1,000 Embeddings (Pago $$) | **10 Embeddings (Centavos)** |

Esta estrategia hace que el proceso sea viables económicamente y extremadamente rápido.
