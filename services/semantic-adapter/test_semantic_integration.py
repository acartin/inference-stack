import asyncio
import os
import sys
import hashlib
from dotenv import load_dotenv

# Asegurar que el path incluya el directorio actual para importar app correctamente
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.embedder import GeminiEmbedder
from app.vector_repo import VectorRepository

async def main():
    # 1. Carga de Entorno
    # Busca el .env en la raíz del proyecto (dos niveles arriba de este script)
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
    print(f"Loading environment from: {env_path}")
    load_dotenv(env_path)

    # Verificar variables críticas
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Error: GOOGLE_API_KEY no encontrada.")
        return
    if not os.getenv("DATABASE_URL"):
        print("❌ Error: DATABASE_URL no encontrada.")
        return

    print("✅ Variables de entorno cargadas.")

    # 2. Validación de Embedding
    print("\n--- Generando Embedding con Gemini ---")
    try:
        embedder = GeminiEmbedder()
        text_to_embed = "Prueba de conexión al stack de inferencia"
        vector = await embedder.embed_query(text_to_embed)
        
        print(f"✅ Embedding generado exitosamente.")
        print(f"   Dimensión del vector: {len(vector)}")
        
        # 3. Validación de Persistencia
        print("\n--- Persistiendo en Vector Store (Postgres) ---")
        repo = VectorRepository()
        
        content_id = "test-integration-001"
        dummy_hash = hashlib.sha256(content_id.encode()).hexdigest()
        doc_data = {
            "content_id": content_id,
            "client_id": "test_client",
            "source": "manual_integration_test",
            "title": "Documento de Prueba de Integración",
            "body_content": text_to_embed,
            "metadata": {"test_timestamp": "2023-12-01T12:00:00Z"},
            "hash": dummy_hash
        }

        repo.upsert_document(doc_data, vector)
        print("✅ Upsert (Insert/Update) realizado exitosamente en Postgres.")

        # 4. Validación de Búsqueda Semántica
        print("\n--- Ejecutando Búsqueda Semántica ---")
        search_query = "stack de inferencia"
        query_vector = await embedder.embed_query(search_query)
        
        results = repo.search_similar(client_id="test_client", query_vector=query_vector, top_k=3)
        
        if results:
            print(f"✅ Búsqueda exitosa. Se encontraron {len(results)} resultados.")
            for r in results:
                print(f"   - [{r['content_id']}] Similarity: {r['similarity']:.4f} | Content: {r['body_content'][:50]}...")
            
            # Verificar si nuestro documento insertado está presente
            found = any(r['content_id'] == content_id for r in results)
            if found:
                print("✨ ÉXITO: El documento insertado fue recuperado semánticamente.")
            else:
                print("⚠️  AVISO: El documento insertado no apareció en los resultados principales.")
        else:
            print("❌ Error: No se devolvieron resultados en la búsqueda.")

    except Exception as e:
        print(f"❌ Error durante la integración: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nPrueba interrumpida.")
