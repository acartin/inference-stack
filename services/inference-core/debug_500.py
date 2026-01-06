
import httpx
import asyncio
import json
from uuid import uuid4

BASE_URL = "http://localhost:8003/api/v1/chat"

async def debug_500():
    async with httpx.AsyncClient() as client:
        print(f"--- 1. Starting New Conversation (id=None) ---")
        payload = {
            "queryText": "Hello", 
            "clientId": "019b4872-51f6-72d3-84c9-45183ff700d0", 
            "conversationId": None
        }
        
        # NOTE: If this fails with FK error, I cannot reproduce the *continuity* bug because I never get a conversation_id.
        # However, I can't query the DB to get a valid client.
        # I will assume for now I might hit the FK error. 
        # But if the user says "First Message OK", they have a valid client.
        # I'll try to find a way. 
        # Maybe I can just use a fake one?
        # Re-reading logs: "Key (client_id)=(...) is not present".
        # I'll try to use a hardcoded one that might exist or just accept catching the *second* error 
        # might be hard if step 1 fails.
        
        # Let's try to run the service locally and mock the repo? No, too complex.
        # I'll try to run the script. If it hits FK error, I'll know I need a valid ID.
        
        resp = await client.post(BASE_URL, json=payload, timeout=30.0)
        print(f"Msg 1 Status: {resp.status_code}")
        print(f"Msg 1 Response: {resp.text}")

        if resp.status_code == 200:
            data = resp.json()
            new_id = data.get("conversation_id")
            print(f"Received ID: {new_id}")
            
            print(f"\n--- 2. Continuing Conversation (id={new_id}) ---")
            payload["conversationId"] = new_id
            payload["queryText"] = "My second message"
            
            resp = await client.post(BASE_URL, json=payload, timeout=30.0)
            print(f"Msg 2 Status: {resp.status_code}")
            print(f"Msg 2 Response: {resp.text}")
        else:
            print("Skipping step 2 due to failure in step 1.")

if __name__ == "__main__":
    asyncio.run(debug_500())
