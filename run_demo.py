import httpx
import time
import asyncio
import json

BASE_URL = "http://localhost:8000/v1"

async def main():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        print("1. Creating User...")
        resp = await client.post("/users/", json={"email": "demo@example.com"})
        if resp.status_code != 201:
            print("Failed to create user:", resp.text)
            # Try to fetch if already exists (for demo purposes)
            return
        user_id = resp.json()["id"]
        print(f"   User created! ID: {user_id}")

        print("\n2. Creating Bank Account...")
        resp = await client.post(f"/accounts/?user_id={user_id}", json={
            "mask": "1234",
            "institution_name": "Chase"
        })
        if resp.status_code != 201:
            print("Failed to create account:", resp.text)
            return
        account_id = resp.json()["id"]
        print(f"   Account created! ID: {account_id}")

        print("\n3. Ingesting Transactions...")
        transactions = [
            {"external_id": "tx1", "date": "2023-10-01", "amount": 15.99, "merchant_name": "Netflix", "description": "NETFLIX subscription"},
            {"external_id": "tx2", "date": "2023-11-01", "amount": 15.99, "merchant_name": "Netflix", "description": "NETFLIX subscription"},
            {"external_id": "tx3", "date": "2023-10-15", "amount": 9.99, "merchant_name": "Spotify", "description": "Spotify Premium"},
            {"external_id": "tx4", "date": "2023-11-15", "amount": 9.99, "merchant_name": "Spotify", "description": "Spotify Premium"},
            {"external_id": "tx5", "date": "2023-11-20", "amount": 4.50, "merchant_name": "Coffee Shop", "description": "Latte"},
            {"external_id": "tx6", "date": "2023-10-05", "amount": 110.00, "merchant_name": "Comcast", "description": "Internet Bill"},
            {"external_id": "tx7", "date": "2023-11-05", "amount": 110.00, "merchant_name": "Comcast", "description": "Internet Bill"},
            {"external_id": "tx8", "date": "2023-10-22", "amount": 14.99, "merchant_name": "Hulu", "description": "Hulu Ad-Free"},
            {"external_id": "tx9", "date": "2023-11-22", "amount": 14.99, "merchant_name": "Hulu", "description": "Hulu Ad-Free"}
        ]
        resp = await client.post("/transactions/ingest", json={
            "account_id": account_id,
            "transactions": transactions
        })
        if resp.status_code != 200:
            print("Failed to ingest:", resp.text)
            return
        print(f"   Ingested {len(resp.json())} transactions.")

        print("\n4. Triggering Audit...")
        resp = await client.post("/audits/", json={"user_id": user_id})
        if resp.status_code != 202:
            print("Failed to trigger audit:", resp.text)
            return
        audit_id = resp.json()["id"]
        print(f"   Audit triggered! ID: {audit_id}")

        print("\n5. Polling for Results...")
        for i in range(15):
            resp = await client.get(f"/audits/{audit_id}")
            data = resp.json()
            status = data["status"]
            print(f"   Status loop {i+1}: {status}")
            
            if status == "completed":
                print("\n✅ AUDIT COMPLETE! Results:")
                print(json.dumps(data.get("raw_result"), indent=2))
                break
            elif status == "failed":
                print("\n❌ AUDIT FAILED Error:")
                print(data.get("error_message"))
                break
            
            time.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
