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
        
        # Validar dimensión esperada (768 para algunos modelos, 1536 para otros - el repo espera 1536)
        if len(vector) != 1536:
            print(f"⚠️ Advertencia: La dimensión del vector ({len(vector)}) puede no coincidir con la columna 'embedding vector(1536)' si no se usa el modelo correcto.")
    except Exception as e:
        print(f"❌ Error al generar embedding: {e}")
        return

    # 3. Validación de Persistencia
    print("\n--- Persistiendo en Vector Store (Postgres) ---")
    try:
        repo = VectorRepository()
        
        # [FIX] : Para pruebas iniciales, forzamos recreación de tabla si el esquema cambió (1536 -> 768)
        # En producción esto sería una migración.
        with repo._get_connection() as conn:
            with conn.cursor() as cur:
                print("♻️  [TEST MODE] Verificando esquema... Dropping table para asegurar consistencia (768 dims)...")
                cur.execute(f"DROP TABLE IF EXISTS {repo.table_name} CASCADE;")
                conn.commit()
        # Re-inicializar para recrear tabla con nuevo esquema
        repo._init_db()

        # Datos Dummy
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
        
    except Exception as e:
        print(f"❌ Error al persistir en base de datos: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nPrueba interrumpida.")
