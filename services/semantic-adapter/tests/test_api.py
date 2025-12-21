from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import sys
import os

# Asegurar que el path incluya el directorio del servicio para importar main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)

# Payload de prueba basado en CanonicalDocument
sample_payload = {
    "content_id": "test-doc-001",
    "source": "manual_test",
    "title": "Documento de Prueba",
    "body_content": "Este es un texto de prueba para verificar el flujo de ingestión. Debe ser fragmentado y vectorizado correctamente.",
    "metadata": {
        "client_id": "client-123",
        "category": "test",
        "ingested_at": "2023-01-01T00:00:00Z"
    },
    "hash": "dummy_hash_12345"
}

@patch("app.api.embedder")
@patch("app.api.repo")
def test_ingest_flow_success(mock_repo, mock_embedder):
    # Configurar Mocks
    # 1. Mock Embedder: Devolver vectores dummy
    # Asumimos que el chunker divide el texto en 1 solo chunk por ser corto
    mock_embedder.embed_documents.return_value = [[0.1, 0.2, 0.3]] 
    
    # 2. Mock Repo: No hacer nada (upsert exitoso)
    mock_repo.upsert_document.return_value = None

    # Ejecutar Request
    response = client.post("/api/v1/ingest", json=sample_payload)

    # Validaciones
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["document_id"] == "test-doc-001"
    assert data["db_records_upserted"] == 1
    
    # Verificar llamadas
    # El chunker es real, así que 'split_text' se ejecutó.
    # El embedder debió ser llamado
    mock_embedder.embed_documents.assert_called_once()
    # El repo debió ser llamado para persistir
    mock_repo.upsert_document.assert_called_once()


@patch("app.api.embedder")
def test_ingest_no_embedder_configured(mock_embedder):
    # Simular que embedder es None (no api key)
    with patch("app.api.embedder", None):
        response = client.post("/api/v1/ingest", json=sample_payload)
        assert response.status_code == 503
        assert "Embedder service not configured" in response.json()["detail"]
