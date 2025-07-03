from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Discord Webhook Service", version="1.0.0")

# Discord webhook URL from environment
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

if not DISCORD_WEBHOOK_URL:
    raise ValueError("DISCORD_WEBHOOK_URL not found in environment variables")

# Pydantic models for request validation
class MessageRequest(BaseModel):
    content: str
    username: str = "Quillix Bot"
    avatar_url: str = None

class EmbedRequest(BaseModel):
    title: str
    description: str
    color: int = 0x00ff00  # Green color
    username: str = "Quillix Bot"
    avatar_url: str = None

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Discord Webhook Service is running"}

@app.post("/send-message")
async def send_message(message: MessageRequest):
    """Send a simple text message to Discord"""
    try:
        payload = {
            "content": message.content,
            "username": message.username
        }
        
        if message.avatar_url:
            payload["avatar_url"] = message.avatar_url
            
        async with httpx.AsyncClient() as client:
            response = await client.post(DISCORD_WEBHOOK_URL, json=payload)
            
        if response.status_code == 204:
            logger.info(f"Message sent successfully: {message.content[:50]}...")
            return {"status": "success", "message": "Message sent to Discord"}
        else:
            logger.error(f"Discord API error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=400, detail="Failed to send message to Discord")
            
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/send-embed")
async def send_embed(embed: EmbedRequest):
    """Send an embed message to Discord"""
    try:
        payload = {
            "username": embed.username,
            "embeds": [{
                "title": embed.title,
                "description": embed.description,
                "color": embed.color
            }]
        }
        
        if embed.avatar_url:
            payload["avatar_url"] = embed.avatar_url
            
        async with httpx.AsyncClient() as client:
            response = await client.post(DISCORD_WEBHOOK_URL, json=payload)
            
        if response.status_code == 204:
            logger.info(f"Embed sent successfully: {embed.title}")
            return {"status": "success", "message": "Embed sent to Discord"}
        else:
            logger.error(f"Discord API error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=400, detail="Failed to send embed to Discord")
            
    except Exception as e:
        logger.error(f"Error sending embed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Discord Webhook Service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)