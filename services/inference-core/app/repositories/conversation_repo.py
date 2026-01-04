import psycopg2
from psycopg2.extras import RealDictCursor, Json
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime
from app.core.config import settings

class ConversationRepository:
    def __init__(self):
        self.dsn = settings.agentic_db_url

    def _get_connection(self):
        return psycopg2.connect(self.dsn, cursor_factory=RealDictCursor)

    def get_or_create_conversation(self, client_id: str, conversation_id: Optional[UUID] = None) -> Dict[str, Any]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                if conversation_id:
                    cur.execute("SELECT * FROM lead_conversations WHERE id = %s", (str(conversation_id),))
                    conv = cur.fetchone()
                    if conv:
                        return dict(conv)
                
                # If not found or not provided, we should ideally link it to a lead.
                # For now, let's create a placeholder lead or just a conversation if the schema allows.
                # Based on previous analysis, lead_id is NOT NULL. 
                # We'll need a way to find or create a lead for this client.
                
                # Hardcoded logic for demo/initial step: find the first lead for this client_id
                # In a real scenario, we'd have a more robust lead identification.
                cur.execute("SELECT id FROM lead_leads WHERE client_id = %s LIMIT 1", (client_id,))
                lead = cur.fetchone()
                
                if not lead:
                    # Create a dummy lead for this client if none exists
                    # We need source_id and full_name for lead_leads
                    new_lead_id = str(uuid4())
                    cur.execute(
                        "INSERT INTO lead_leads (id, client_id, source_id, full_name) VALUES (%s, %s, %s, %s)",
                        (new_lead_id, client_id, 14, f"User {client_id[:8]}")
                    )
                    lead_id = new_lead_id
                else:
                    lead_id = lead['id']

                new_conv_id = str(conversation_id or uuid4())
                cur.execute(
                    """
                    INSERT INTO lead_conversations (id, lead_id, platform, messages)
                    VALUES (%s, %s, %s, %s)
                    RETURNING *
                    """,
                    (new_conv_id, lead_id, 'webchat', Json([]))
                )
                return dict(cur.fetchone())

    def get_conversation(self, conversation_id: UUID) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM lead_conversations WHERE id = %s", (str(conversation_id),))
                conv = cur.fetchone()
                return dict(conv) if conv else None

    def update_conversation(self, conversation_id: UUID, new_messages: List[Dict[str, Any]], summary: Optional[str] = None):
        # Calcular contadores
        total = len(new_messages)
        lead_msgs = len([m for m in new_messages if m.get('role') == 'user'])
        bot_msgs = len([m for m in new_messages if m.get('role') == 'assistant'])
        
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE lead_conversations 
                    SET 
                        messages = %s, 
                        summary = %s, 
                        updated_at = %s,
                        last_message_at = %s,
                        total_messages = %s,
                        lead_messages = %s,
                        bot_messages = %s
                    WHERE id = %s
                    """,
                    (
                        Json(new_messages), 
                        summary, 
                        datetime.now(), 
                        datetime.now(),
                        total,
                        lead_msgs,
                        bot_msgs,
                        str(conversation_id)
                    )
                )
                conn.commit()

    def get_system_prompt(self, client_id: str, slug: str = 'primary_chat') -> str:
        """
        Recupera el prompt de sistema para un cliente específico o el global por defecto.
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # 1. Intentar obtener prompt específico del cliente
                cur.execute(
                    "SELECT prompt_text FROM lead_ai_prompts WHERE client_id = %s AND slug = %s AND is_active = true",
                    (client_id, slug)
                )
                row = cur.fetchone()
                if row:
                    return row['prompt_text']
                
                # 2. Intentar obtener prompt global (client_id es NULL)
                cur.execute(
                    "SELECT prompt_text FROM lead_ai_prompts WHERE client_id IS NULL AND slug = %s AND is_active = true",
                    (slug,)
                )
                row = cur.fetchone()
                if row:
                    return row['prompt_text']
                
                # 3. Fallback de seguridad en código
                return "Eres un asistente técnico. Responde basándote exclusivamente en el contexto:\n\n{context_text}"

    def update_lead_scores(self, lead_id: str, scores: Dict[str, Any]):
        """
        Actualiza los puntajes de un lead. El trigger fn_calculate_lead_score
        se encargará de actualizar los def_id y el total automáticamente.
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE lead_leads 
                    SET 
                        score_engagement = %s,
                        score_finance = %s,
                        score_timeline = %s,
                        score_match = %s,
                        score_info = %s,
                        updated_at = %s
                    WHERE id = %s
                    """,
                    (
                        scores['score_engagement'],
                        scores['score_finance'],
                        scores['score_timeline'],
                        scores['score_match'],
                        scores['score_info'],
                        datetime.now(),
                        lead_id
                    )
                )
                conn.commit()
