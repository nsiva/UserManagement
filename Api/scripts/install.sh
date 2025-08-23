#!/bin/bash

# Install UV and set up the environment
echo "Installing UV package manager..."

# Install UV if not present
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="/Users/siva/.local/bin:$PATH"
fi

# Create virtual environment
echo "Creating UV virtual environment..."
uv venv --python 3.11

# Install dependencies
echo "Installing dependencies..."
uv pip install fastapi uvicorn 'passlib[bcrypt]' 'python-jose[cryptography]' supabase pyotp 'qrcode[pil]' python-dotenv httpx pydantic-settings 'pydantic[email]'

echo "✅ Setup complete!"
echo "Activate the environment with: source .venv/bin/activate"
echo "Start the server with: ./scripts/start.sh"