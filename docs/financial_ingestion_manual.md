# Manual de Implementación: Datos Financieros (Costa Rica)

Este documento define la estrategia para ingerir información bancaria y financiera (tasas, requisitos, plazos) que permitirá a la IA asesorar sobre capacidad de pago y opciones de crédito.

---

## 1. Naturaleza del Dato: Contexto Global vs Específico

A diferencia de las propiedades (que son de un cliente específico), la información financiera suele ser **pública y transversal**.
*   **Decisión Arquitectónica**: Se recomienda cargar estos datos bajo un `client_id` especial del sistema (ej: "SYSTEM" o UUID fijo de "Admin") o usar una categoría especial `financial_context` que el prompt del sistema sepa consultar globalmente.

---

## 2. Estructura del Dato: Texto Natural (Recomendado)

**¡Simplifica tu ETL!** No necesitas parsear cada tasa o plazo en campos JSON complejos. La IA entiende mejor el lenguaje natural.

### Opción A: Texto Web Directo (Copy-Paste)
Puedes simplemente extraer el texto de la página del producto ("Términos y Condiciones", "Beneficios") y enviarlo tal cual.

> **Ejemplo de Contenido Válido:**
> *"Beneficios de la Hipoteca Verde del BCR: Tasa del 7.5% fija por 2 años. Se requiere certificación EDGE. Financiamiento de gastos legales incluido. Plazo hasta 30 años."*

La IA leerá esto y entenderá las reglas sin que tú tengas que programar un parser para cada banco.

### Opción B: Híbrido (Texto + Metadatos Básicos)
Usa el texto web para el `body_content` y usa los metadatos JSON solo para filtros duros (ej: moneda, banco).

---

## 3. Lógica del Proceso Batch (Quincenal)

Al ser un proceso menos frecuente (cada 15 días), la eficiencia de "Local Diff" es menos crítica, pero la **calidad del texto** es vital.

1.  **Agrupación**: El script debe agrupar por Institución Financiera.
2.  **Generación**: Crear un documento por cada Producto Financiero relevante.
3.  **Ingesta**:
    *   **Endpoint**: `/api/v1/ingest`
    *   **Client ID**: Recomiendo usar un UUID reservado para "Conocimiento Global" (ej: el UUID del Admin de la plataforma).
    *   **Category**: `financial_products`.

---

## 4. Payload Sugerido

```json
{
  "content_id": "fin_{banco}_{producto_id}",
  "source": "financial_etl",
  "title": "Condiciones Crédito {Banco} - {Producto}",
  "body_content": "{texto_narrativo_generado}",
  "hash": "{sha256}",
  "metadata": {
    "client_id": "UUID_DEL_SISTEMA_GLOBAL", 
    "category": "financial_products",
    "bank": "Banco Nacional",
    "currency": "USD",
    "min_rate": 7.5
  }
}
```

---

## 5. Uso en Inferencia (RAG)

Cuando el Lead Analyzer detecte "Intención Financiera" (`finance > 20`), el sistema buscará activamente en la categoría `financial_products`.

*   **Prompt del Bot**: *"Usa la información de tasas actuales en Costa Rica para estimar la cuota mensual. Si el cliente gana $3,000, recomiéndale bancos que pidan menos de ese ingreso."*

Esta estructura permite que el bot pase de ser un vendedor a un **Asesor Hipotecario** informado con datos reales del mercado.
