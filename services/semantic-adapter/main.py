from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging
from app.api import router

# Configuración de logs según convenciones
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("semantic-adapter")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Lógica de encendido
    logger.info("🚀 Iniciando Semantic Adapter en VM 102...")
    try:
        # Aquí llamarás a la verificación de pgvector en VM 101
        # await vector_repo.verify_connection()
        logger.info("✅ Conexión con pgvector establecida.")
    except Exception as e:
        logger.error(f"❌ Fallo crítico en el arranque: {e}")
    
    yield
    # Lógica de apagado (si fuera necesaria)
    logger.info("🛑 Apagando Semantic Adapter...")

app = FastAPI(
    title="Semantic Adapter API",
    version="1.0.0",
    lifespan=lifespan
)

# Inclusión de rutas con el prefijo definido
app.include_router(router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "semantic-adapter"}