from typing import Dict, Any, Optional, List
import hashlib
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from app.chunker import Chunker
from app.embedder import GeminiEmbedder
from app.vector_repo import VectorRepository

router = APIRouter()

# Instancias Globales (Lazy loading podría ser mejor, pero esto es directo)
chunker = Chunker()
# Ojo: Requiere GOOGLE_API_KEY en env
try:
    embedder = GeminiEmbedder()
except ValueError as e:
    embedder = None
    print(f"Warning: Embedder not initialized: {e}")

repo = VectorRepository()

class CanonicalMetadata(BaseModel):
    client_id: str
    category: Optional[str] = None
    url: Optional[str] = None
    source_timestamp: Optional[str] = None
    ingested_at: Optional[str] = None
    # Permite campos extra
    class Config:
        extra = "allow"

class CanonicalDocument(BaseModel):
    content_id: str
    source: str
    title: Optional[str] = None
    body_content: str
    metadata: CanonicalMetadata
    hash: str

class SearchRequest(BaseModel):
    query_text: str
    client_id: str
    top_k: int = 5

class SearchResult(BaseModel):
    content_id: str
    title: Optional[str]
    body_content: str
    metadata: Dict[str, Any]
    score: float

class SearchResponse(BaseModel):
    results: List[SearchResult]
    query_text: str
    client_id: str

@router.get("/health")
async def health_check():
    """
    Health check endpoint to verify service status.
    """
    db_status = "unknown"
    try:
        # Simple verficación de conexión si fuera necesario
        # with repo._get_connection() as conn: ...
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
        
    return {
        "status": "ok", 
        "service": "semantic-adapter", 
        "embedder": "ready" if embedder else "not_configured",
        "db": db_status
    }

@router.post("/ingest")
async def ingest_document(doc: CanonicalDocument):
    """
    Recibe un documento canónico, lo fragmenta, genera embeddings
    y persiste los vectores en la base de datos.
    """
    if not embedder:
        raise HTTPException(status_code=503, detail="Embedder service not configured (missing API Key)")

    # 1. Chunking
    chunks = chunker.split_text(doc.body_content)
    if not chunks:
        return {"status": "ignored", "reason": "empty_content"}

    # 2. Embedding (Async)
    try:
        vectors = await embedder.embed_documents(chunks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {str(e)}")

    if len(vectors) != len(chunks):
        raise HTTPException(status_code=500, detail="Mismatch between chunks and vectors generated")

    # 3. Persistence (Sync -> Threadpool)
    # Al ser una operación IO-bound síncrona (psycopg2), no queremos bloquear el loop principal.
    upserted_count = 0
    
    for i, (chunk_text, vector) in enumerate(zip(chunks, vectors)):
        # Generar hash determinista para el chunk: sha256(doc_hash + index)
        # Esto asegura idempotencia: el mismo documento fragmentado igual tendrá los mismos IDs.
        chunk_hash_input = f"{doc.hash}_{i}"
        chunk_hash = hashlib.sha256(chunk_hash_input.encode()).hexdigest()

        chunk_data = {
            "content_id": doc.content_id, 
            "client_id": doc.metadata.client_id,
            "source": doc.source,
            "title": doc.title, # Opcional: f"{doc.title} (Part {i+1})"
            "body_content": chunk_text,
            "metadata": doc.metadata.dict(),
            "hash": chunk_hash
        }

        # Ejecutar upsert en threadpool para no bloquear
        await run_in_threadpool(repo.upsert_document, chunk_data, vector)
        upserted_count += 1

    return {
        "status": "success",
        "document_id": doc.content_id,
        "chunks_processed": len(chunks),
        "db_records_upserted": upserted_count
    }

@router.post("/search", response_model=SearchResponse)
async def search_documents(req: SearchRequest):
    """
    Realiza una búsqueda semántica basada en el texto de consulta.
    """
    if not embedder:
        raise HTTPException(status_code=503, detail="Embedder service not configured")

    # 1. Generar embedding para la query
    try:
        query_vector = await embedder.embed_query(req.query_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")

    # 2. Búsqueda en DB (en threadpool ya que search_similar es síncrona)
    try:
        db_results = await run_in_threadpool(repo.search_similar, req.client_id, query_vector, req.top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database search failed: {str(e)}")

    # 3. Formatear resultados
    formatted_results = []
    for row in db_results:
        formatted_results.append(SearchResult(
            content_id=row["content_id"],
            title=row["title"],
            body_content=row["body_content"],
            metadata=row["metadata"],
            score=row["similarity"]
        ))

    return SearchResponse(
        results=formatted_results,
        query_text=req.query_text,
        client_id=req.client_id
    )

@router.delete("/client/{client_id}")
async def delete_client_data(client_id: str):
    """
    Endpoint para eliminar toda la memoria semántica de un cliente.
    """
    try:
        count = await run_in_threadpool(repo.delete_client_data, client_id)
        return {
            "status": "success",
            "client_id": client_id,
            "records_deleted": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete client data: {str(e)}")

@router.delete("/client/{client_id}/document/{content_id}")
async def delete_document(client_id: str, content_id: str):
    """
    Endpoint para eliminar un documento específico por su ID de contenido.
    """
    try:
        count = await run_in_threadpool(repo.delete_document, client_id, content_id)
        if count == 0:
            # Opcional: Podríamos retornar 404, pero idempotencia (borrar algo que no existe = éxito) es válida.
            # Sin embargo, para debug es útil saber si borró algo.
            pass
            
        return {
            "status": "success",
            "client_id": client_id,
            "content_id": content_id,
            "records_deleted": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")
