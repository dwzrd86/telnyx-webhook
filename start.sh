#!/bin/bash
set -e

echo "🚀 Telnyx Webhook starting..."

# Install dependencies
pip install -r requirements.txt

# Run webhook
exec uvicorn app:app --host 0.0.0.0 --port $PORT
