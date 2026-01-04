from fastapi import FastAPI
import logging
from app.api.chat import router as chat_router
from app.core.config import settings

# Configuración de logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("inference-core")

app = FastAPI(
    title="Inference Core API",
    version="1.0.0",
    description="Motor central de orquestación RAG y Chatbot"
)

# Inclusión de rutas
app.include_router(chat_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Inference Core is running", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

