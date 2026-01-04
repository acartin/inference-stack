from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging
from app.api import router

# Configuración de logs según convenciones
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("semantic_adapter")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Lógica de encendido
    logger.info("🚀 Iniciando Semantic Adapter...")
    yield
    # Lógica de apagado
    logger.info("🛑 Apagando Semantic Adapter...")

app = FastAPI(
    title="Semantic Adapter API",
    version="1.0.0",
    lifespan=lifespan
)

# Inclusión de rutas con el prefijo oficial
app.include_router(router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "semantic-adapter"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)