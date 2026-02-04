#!/usr/bin/env python3
"""
Telnyx SMS Webhook Handler
Receives incoming SMS and forwards to Mizzle
"""

import os
import httpx
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Telnyx SMS Webhook",
    description="Receives SMS from Telnyx and alerts Mizzle",
    version="1.0.0"
)

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
MIZZLE_ENDPOINT = os.getenv("MIZZLE_ENDPOINT", "http://localhost:8080")


class TelnyxWebhook(BaseModel):
    """Telnyx webhook payload"""
    from_: str = ""
    to: str = ""
    text: str = ""
    message_timestamp: Optional[str] = None


@app.post("/webhook/sms")
async def receive_sms(request: Request):
    """Receive SMS from Telnyx"""
    try:
        payload = await request.json()
        
        # Extract message details
        from_num = payload.get("from", "Unknown")
        to_num = payload.get("to", "Unknown")
        text = payload.get("text", "")
        timestamp = payload.get("message_timestamp", "")
        
        logger.info(f"📱 SMS from {from_num} to {to_num}: {text}")
        
        # Forward to Telegram
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            message = f"📱 **SMS Received**\n\nFrom: {from_num}\nTo: {to_num}\n\n{text}"
            
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id": TELEGRAM_CHAT_ID,
                        "text": message,
                        "parse_mode": "Markdown"
                    }
                )
        
        # Forward to Mizzle endpoint
        if MIZZLE_ENDPOINT:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{MIZZLE_ENDPOINT}/sms/received",
                    json={
                        "from": from_num,
                        "to": to_num,
                        "text": text,
                        "timestamp": timestamp
                    }
                )
        
        return {"status": "received", "message": "SMS processed"}
        
    except Exception as e:
        logger.error(f"Error processing SMS: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "telnyx-webhook"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Telnyx SMS Webhook",
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
