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

    async def analyze_conversation(self, history: List[Dict[str, Any]]) -> LeadScoringResult:
        """
        Analiza el historial de la conversación y devuelve un objeto de scoring.
        """
        # Convert history to text
        conversation_text = ""
        for msg in history:
            role = "Usuario" if msg['role'] == 'user' else "Asistente"
            conversation_text += f"{role}: {msg.get('text', msg.get('content', ''))}\n"

        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un experto en calificación de leads inmobiliarios. Tu tarea es analizar la conversación proporcionada y asignar un puntaje (score) para 5 criterios específicos.

CRITERIOS DE CALIFICACIÓN:

1. ENGAGEMENT (Rango: -20 a 30):
   - Mide el interés del usuario. (30 = Pide cita o deja datos claros, 10-20 = Hace preguntas de negocio, -20 = Insulta o pide que lo borren).
2. FINANCE (Rango: -10 a 30):
   - Capacidad de pago detectada. (30 = Cash/Contado, 20-25 = Crédito pre-aprobado/Ingresos altos, -10 = Dice no tener dinero).
3. TIMELINE (Rango: 0 a 20):
   - Plazo de compra. (20 = Inmediato/Este mes, 15 = 1-3 meses, 5 = Solo viendo/Largo plazo).
4. MATCH (Rango: 0 a 15):
   - Ajuste al producto. (15 = Busca exactamente lo que el contexto ofrece, 7-9 = Interés general, 0 = Busca algo totalmente distinto).
5. INFO (Rango: -3 a 5):
   - Calidad del perfil. (5 = Nombre, Celular y Email detectados, 1-3 = Faltan datos críticos, -3 = Datos falsos/Evasivo).

INSTRUCCIONES:
- Analiza la INTENCIÓN del usuario, independientemente de si el Asistente pudo resolver la duda o no.
- Devuelve un JSON con los 5 scores y un campo 'reasoning' corto en español.
- Si no hay información suficiente para un criterio, usa el valor neutro (0).
"""),
            ("human", "Analiza la siguiente conversación y devuelve el scoring en formato JSON:\n\n{history}")
        ])

        try:
            # Forzamos respuesta estructurada (JSON)
            structured_llm = self.llm.with_structured_output(LeadScoringResult)
            chain = prompt | structured_llm
            result = await chain.ainvoke({"history": conversation_text})
            return result
        except Exception as e:
            logger.error(f"Error analyzing conversation: {e}")
            # Fallback en caso de error
            return LeadScoringResult(reasoning="Error en el análisis automático.")
