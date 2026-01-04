# Manual de Implementación: Interfaz de Chat

Este documento define cómo el servidor WWW (Laravel/Filament) debe interactuar con el Inference Stack para construir la experiencia de chat.

---

## 1. Arquitectura de Estado (¿Dónde vive la memoria?)

**El Source of Truth (Fuente de la Verdad) es el Inference Stack.**
*   El servidor WWW actúa como una **Vista (View)**.
*   El servidor AI actúa como el **Controlador y Modelo**.

Toda la historia del chat reside en la base de datos `agentic` (tabla `lead_conversations`, columna `messages`), gestionada exclusivamente por los endpoints del Inference Core.

### Responsabilidad de WWW
*   **No debe duplicar** el historial en su propia base de datos (redundancia peligrosa).
*   **Sí puede** cachear el último estado para mostrarlo rápido, pero siempre debe refrescar desde la API.

---

## 2. Flujo de Mensajería (Paso a Paso)

### A. Usuario envía mensaje
1.  **Frontend**: Usuario escribe "Hola" y pulsa Enviar.
2.  **WWW**: Hace POST a su propio backend.
3.  **WWW -> AI**: Llama a `POST http://192.168.0.32:8003/api/v1/chat`.
    *   **Payload**: `{"message": "Hola", "client_id": "...", "lead_id": "..."}`.
    *   *Nota: Si es el primer mensaje, `conversation_id` es null.*

### B. AI Procesa (Inferencia)
1.  El `Inference Core` recibe el mensaje.
2.  Recupera el historial previo de `lead_conversations`.
3.  Ejecuta RAG (busca en Semantic Adapter) y genera respuesta con Gemini.
4.  **Persistencia**: Guarda user_msg + bot_msg en la columna `messages` de la DB agentic.
5.  **Respuesta**: Retorna `{"response": "Hola, ¿en qué puedo ayudarte?", "conversation_id": "..."}`.

### C. WWW Renderiza
1.  Recibe la respuesta JSON.
2.  Pinta el mensaje del bot en la UI.

---

## 3. Recuperación de Historial (Al recargar página)

Cuando el usuario entra de nuevo al chat:
**No leas de tu DB local.** Lee de la fuente real.

*   **Endpoint**: `GET http://192.168.0.32:8003/api/v1/chat/{conversation_id}`
*   **Respuesta**: Array completo de objetos `{"role": "user/assistant", "content": "..."}`.

---

## 4. Diseño de UI (Sugerencias)

*   **Indicador de "Escribiendo..."**: La inferencia RAG toma entre 2-4 segundos. Muestra un "Thinking..." real.
*   **Citas/Fuentes**: La API devuelve `sources`. Úsalas para mostrar "Fuente: Manual de Ventas, pág 3" debajo de la respuesta. Esto da mucha credibilidad.
*   **Contexto Financiero**: Si el bot detecta intención financiera, mostrará widgets (gracias al Lead Scoring). La UI debe estar preparada para renderizar "Cards de Bancos" si la API los devuelve en el futuro.

---

## Resumen para Developer (Laravel)

1.  **NO crees una tabla `chat_messages`**.
2.  Usa `conversation_id` como tu puntero principal.
3.  Todo el tráfico de chat es un proxy hacia el puerto `8003`.
