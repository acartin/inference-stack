
import httpx
import asyncio
import json
from uuid import uuid4

BASE_URL = "http://localhost:8005/api/v1"

TEST_DOC = {
    "content_id": "test-doc-001",
    "source": "verification_script",
    "title": "Verification Test Document",
    "body_content": "This is a test document to verify the ingestion API. It contains some text about verification.",
    "hash": "hash_123456789",
    "metadata": {
        "client_id": str(uuid4()),
        "category": "verification",
        "original_filename": "test.pdf"
    }
}

async def run_verification():
    async with httpx.AsyncClient(timeout=10.0) as client:
        print(f"Checking Service Health at {BASE_URL}/health ...")
        resp = await client.get(f"{BASE_URL}/health")
        print(f"Health: {resp.status_code} - {resp.json()}")
        if resp.status_code != 200:
            print("Service unhealth/unreachable. Aborting.")
            return

        print("\n--- 1. Testing Ingest (POST /ingest) ---")
        resp = await client.post(f"{BASE_URL}/ingest", json=TEST_DOC)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"Ingest failed! Body: {resp.text}")
            return
            
        print(f"Response: {resp.json()}")
        
        # Verify response structure
        data = resp.json()
        assert data['status'] == 'success'
        assert data['document_id'] == TEST_DOC['content_id']
        print(">> Ingest Success")

        print("\n--- 2. Testing Delete Document (DELETE /client/.../document/...) ---")
        client_id = TEST_DOC['metadata']['client_id']
        content_id = TEST_DOC['content_id']
        resp = await client.delete(f"{BASE_URL}/client/{client_id}/document/{content_id}")
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")
        assert resp.status_code == 200
        assert resp.json()['status'] == 'success'
        print(">> Delete Document Success")

        print("\n--- 3. Testing Delete Client (DELETE /client/...) ---")
        # Ingest again to have something to delete
        await client.post(f"{BASE_URL}/ingest", json=TEST_DOC)
        
        resp = await client.delete(f"{BASE_URL}/client/{client_id}")
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")
        assert resp.status_code == 200
        assert resp.json()['status'] == 'success'
        print(">> Delete Client Success")

        print("\nALL TESTS PASSED")

if __name__ == "__main__":
    asyncio.run(run_verification())
