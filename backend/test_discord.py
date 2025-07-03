import asyncio
import httpx
from dotenv import load_dotenv
import os

load_dotenv()

async def test_discord_webhook():
    """Test the Discord webhook directly"""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    if not webhook_url:
        print("DISCORD_WEBHOOK_URL not found in environment")
        return
    
    # Test message
    payload = {
        "content": "🚀 Test message from Quillix backend service!",
        "username": "Quillix Bot"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(webhook_url, json=payload)
            if response.status_code == 204:
                print("✅ Test message sent successfully!")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_discord_webhook())