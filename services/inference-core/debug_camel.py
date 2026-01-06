
import httpx
import asyncio
import json
from uuid import uuid4

BASE_URL = "http://localhost:8003/api/v1/chat"

async def debug_camel_case():
    async with httpx.AsyncClient() as client:
        print(f"--- Testing CamelCase Payload ---")
        # Payload mimicking the user's log
        payload = {
            "queryText": "Hello from CamelCase", # Assuming they use queryText too? Or query_text? User didn't show this part but likely consistent.
            # Let's try mix just in case: client sent clientId
            "clientId": str(uuid4()),
            "conversationId": None,
            "leadId": "test_lead_123",
            # We strictly need query_text field name unless we alias it too.
            # I'll assume they might send queryText too, but let's test just client_id mismatch first if query_text was correct.
            "query_text": "Hello (snake_case key)" 
        }
        
        # Test 1: Snake query, Camel others
        print("Test 1: Snake query_text, Camel clientId")
        resp = await client.post(BASE_URL, json=payload)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")

        # Test 2: All Camel
        print("\nTest 2: All CamelCase (queryText)")
        payload_2 = {
            "queryText": "Hello",
            "clientId": str(uuid4()),
            "conversationId": None
        }
        resp = await client.post(BASE_URL, json=payload_2)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")

if __name__ == "__main__":
    asyncio.run(debug_camel_case())
