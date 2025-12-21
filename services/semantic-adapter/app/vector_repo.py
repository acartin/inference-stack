import os
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from pgvector.psycopg2 import register_vector


class VectorRepository:
    def __init__(self):
        self.conn_url = os.getenv("DATABASE_URL")
        self.table_name = "semantic_items"
        self._init_db()

    def _get_connection(self):
        conn = psycopg2.connect(self.conn_url)
        register_vector(conn)  # Registra el tipo vector en la conexión
        return conn

    def _init_db(self):
        """
        Crea la tabla semantic_items basada en el esquema canónico
        y prepara el índice vectorial.
        """
        query = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

            -- Identidad lógica
            content_id TEXT NOT NULL,
            client_id TEXT NOT NULL,
            source TEXT NOT NULL,

            -- Contenido
            title TEXT,
            body_content TEXT NOT NULL,

            -- Metadata flexible para filtros semánticos
            metadata JSONB,

            -- Control de idempotencia / versionado
            hash TEXT UNIQUE,

            -- Vector embedding
            -- 1536: OpenAI
            -- 768 : Gemini (text-embedding-004) / MiniLM
            embedding vector(768),

            -- Auditoría
            created_at TIMESTAMP DEFAULT now(),
            updated_at TIMESTAMP DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS {self.table_name}_embedding_idx
        ON {self.table_name}
        USING hnsw (embedding vector_cosine_ops);

        CREATE INDEX IF NOT EXISTS {self.table_name}_client_idx
        ON {self.table_name} (client_id);
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                conn.commit()

    def upsert_document(self, doc_data: dict, embedding: list):
        """
        Inserta o actualiza un documento semántico.
        La deduplicación se basa exclusivamente en el hash.
        """
        query = f"""
        INSERT INTO {self.table_name}
        (
            content_id,
            client_id,
            source,
            title,
            body_content,
            metadata,
            hash,
            embedding
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (hash) DO UPDATE SET
            title = EXCLUDED.title,
            body_content = EXCLUDED.body_content,
            metadata = EXCLUDED.metadata,
            embedding = EXCLUDED.embedding,
            updated_at = now();
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    (
                        doc_data["content_id"],
                        doc_data["client_id"],
                        doc_data["source"],
                        doc_data.get("title"),
                        doc_data["body_content"],
                        Json(doc_data.get("metadata", {})),
                        doc_data["hash"],
                        embedding,
                    ),
                )
                conn.commit()
