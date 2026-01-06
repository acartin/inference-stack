import logging
import json
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import settings
from app.models.chat import LeadScoringResult

logger = logging.getLogger("inference-core.analyzer")

class LeadAnalyzer:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0
        )

    async def analyze_conversation(self, history: List[Dict[str, Any]], catalogs: Dict[str, Any] = None) -> LeadScoringResult:
        """
        Analiza el historial de la conversación y devuelve un objeto de scoring y extracción de datos.
        """
        catalogs = catalogs or {}
        currencies = catalogs.get('currencies', [])
        preferences = catalogs.get('preferences', [])
        
        # Convert history to text
        conversation_text = ""
        for msg in history:
            role = "Usuario" if msg['role'] == 'user' else "Asistente"
            conversation_text += f"{role}: {msg.get('text', msg.get('content', ''))}\n"

        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""Eres un experto en calificación de leads inmobiliarios. Tu tarea es analizar la conversación y:
1. Asignar puntajes (scores) para 5 criterios.
2. EXTRAER INFORMACIÓN del perfil del usuario (Nombre, Email, Teléfono, Finanzas) si está presente explícitamente.

CRITERIOS DE CALIFICACIÓN:
1. ENGAGEMENT (-20 a 30): Interés del usuario.
2. FINANCE (-10 a 30): Capacidad de pago.
3. TIMELINE (0 a 20): Plazo de compra.
4. MATCH (0 a 15): Ajuste al producto.
5. INFO (-3 a 5): Calidad del perfil.

INSTRUCCIONES DE EXTRACCIÓN AUTOMÁTICA:
- Si el usuario menciona su NOMBRE COMPLETO, EMAIL o TELÉFONO, extráelos en los campos `extracted_name`, `extracted_email`, `extracted_phone`.
- Si menciona INGRESOS MENSUALES, extráelo en `extracted_income` (solo el número).
- Si menciona DEUDAS MENSUALES, extráelo en `extracted_debts` (solo el número).
- Si menciona una MONEDA (Dólares, Colones, etc.), intenta mapearla a uno de estos códigos válidos: {{currencies}}. Si lo encuentras, pon el código en `extracted_currency_id`.
- Si indica una PREFERENCIA DE CONTACTO (WhatsApp, Email, Llamada), intenta mapearla a uno de estos IDs válidos: {{preferences}}. Si hay coincidencia, pon el UUID en `extracted_contact_pref_id`.

SI NO ENCUENTRAS EL DATO, DÉJALO NULL. NO INVENTES DATOS.

Devuelve un JSON con los scores, el reasoning y los campos extraídos.
"""),
            ("human", "Analiza la siguiente conversación y devuelve el scoring e información extraída en formato JSON:\n\n{history}")
        ])

        try:
            # Forzamos respuesta estructurada (JSON)
            structured_llm = self.llm.with_structured_output(LeadScoringResult)
            chain = prompt | structured_llm
            result = await chain.ainvoke({
                "history": conversation_text,
                "currencies": currencies,
                "preferences": preferences
            })
            return result
        except Exception as e:
            logger.error(f"Error analyzing conversation: {e}")
            # Fallback en caso de error
            return LeadScoringResult(reasoning="Error en el análisis automático.")
