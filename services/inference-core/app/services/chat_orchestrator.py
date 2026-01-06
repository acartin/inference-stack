import httpx
import logging
import asyncio
from typing import List, Dict, Any
from uuid import UUID
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.core.config import settings
from app.models.chat import ChatMessageRequest, ChatMessageResponse, SourceDocument
from app.repositories.conversation_repo import ConversationRepository
from app.services.lead_analyzer import LeadAnalyzer

logger = logging.getLogger("inference-core.orchestrator")

class ChatOrchestrator:
    def __init__(self):
        self.repo = ConversationRepository()
        self.analyzer = LeadAnalyzer()
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.2
        )
        self.semantic_url = f"{settings.SEMANTIC_ADAPTER_URL}/api/v1/search"

    async def chat(self, request: ChatMessageRequest) -> ChatMessageResponse:
        # 1. Get/Create conversation history
        conversation = self.repo.get_or_create_conversation(request.client_id, request.conversation_id)
        conv_id = conversation['id']
        history = conversation.get('messages', [])

        # 2. Retrieve Context from Semantic Adapter
        context_docs = await self._get_semantic_context(request.query_text, request.client_id)
        
        # 3. Retrieve Dynamic System Prompt
        system_prompt_template = self.repo.get_system_prompt(request.client_id)
        
        # 4. Build Prompt
        context_text = "\n\n".join([f"Source {i+1}: {doc['body_content']}" for i, doc in enumerate(context_docs)])
        
        # Create a System Prompt Template from the DB string
        # This handles {context_text} as a variable automatically
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt_template),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])

        # Convert history format for LangChain
        lc_history = []
        for msg in history[-10:]: # Last 10 messages for context
            if msg['role'] == 'user':
                lc_history.append(HumanMessage(content=msg.get('content') or msg.get('text', '')))
            else:
                lc_history.append(AIMessage(content=msg.get('content') or msg.get('text', '')))

        # 4. Generate Answer
        chain = prompt | self.llm
        response = await chain.ainvoke({
            "context_text": context_text,
            "history": lc_history,
            "input": request.query_text
        })
        answer = response.content

        new_history = history + [
            {"role": "user", "content": request.query_text, "timestamp": str(datetime.now())},
            {"role": "assistant", "content": answer, "timestamp": str(datetime.now())}
        ]
        self.repo.update_conversation(UUID(conv_id), new_history)

        # 6. Background Task: Analyze Lead Scoring
        # We find the lead_id from the conversation
        lead_id = conversation.get('lead_id')
        if lead_id:
            # Fetch Catalogs
            catalogs = self.repo.get_catalogs()
            asyncio.create_task(self._run_lead_analysis(lead_id, new_history, catalogs))

        # 7. Format Response
        sources = [
            SourceDocument(
                content_id=doc['content_id'],
                title=doc['title'],
                body_content=doc['body_content'],
                score=doc['score'],
                metadata=doc['metadata']
            ) for doc in context_docs
        ]

        return ChatMessageResponse(
            answer=answer,
            sources=sources,
            conversation_id=UUID(conv_id)
        )

    async def _get_semantic_context(self, query: str, client_id: str) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.semantic_url,
                    json={
                        "query_text": query,
                        "client_id": client_id,
                        "top_k": 3
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                return data.get("results", [])
            except Exception as e:
                logger.error(f"Error calling semantic adapter: {e}")
                return []

    async def _run_lead_analysis(self, lead_id: str, history: List[Dict[str, Any]], catalogs: Dict[str, Any]):
        """
        Helper para ejecutar el análisis de lead en background.
        """
        try:
            scoring_result = await self.analyzer.analyze_conversation(history, catalogs)
            self.repo.update_lead_scores(lead_id, scoring_result.dict())
            logger.info(f"Lead {lead_id} scored: {scoring_result.reasoning}")
        except Exception as e:
            logger.error(f"Error in background lead analysis: {e}")

    def get_conversation_history(self, conversation_id: UUID) -> List[Dict[str, Any]]:
        conversation = self.repo.get_conversation(conversation_id)
        if not conversation:
            return []
        # Return the raw messages list
        return conversation.get('messages', [])
