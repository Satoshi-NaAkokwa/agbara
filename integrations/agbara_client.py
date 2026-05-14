"""
Agbara OpenAI-Compatible Client
Use this to integrate Agbara with any application that supports OpenAI SDK.
"""

import os
from openai import OpenAI

# Agbara API Configuration
AGBARA_API_KEY = "agbara_sk_live_f7a9b2c4d6e8f0a1b2c3d4e5f6a7b8c9"
AGBARA_API_BASE = "http://localhost:8000/v1"

# Initialize Client
client = OpenAI(
    api_key=AGBARA_API_KEY,
    base_url=AGBARA_API_BASE
)

def chat(message: str, model: str = "agbara") -> str:
    """Send a chat message to Agbara."""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": message}]
    )
    return response.choices[0].message.content

def chat_igbo(message: str) -> str:
    """Chat with Igbo language expert."""
    return chat(message, model="agbara-igbo")

def chat_code(message: str) -> str:
    """Chat with code expert."""
    return chat(message, model="agbara-code")

def get_proverb() -> dict:
    """Get an Igbo proverb."""
    import requests
    response = requests.get(
        f"{AGBARA_API_BASE.rstrip('/v1')}/v1/igbo/proverb",
        headers={"Authorization": f"Bearer {AGBARA_API_KEY}"}
    )
    return response.json()

def translate(text: str, direction: str = "igbo-to-english") -> dict:
    """Translate between Igbo and English."""
    import requests
    response = requests.post(
        f"{AGBARA_API_BASE.rstrip('/v1')}/v1/igbo/translate",
        headers={
            "Authorization": f"Bearer {AGBARA_API_KEY}",
            "Content-Type": "application/json"
        },
        json={"text": text, "direction": direction}
    )
    return response.json()

# Example Usage
if __name__ == "__main__":
    print("=== Agbara API Client ===\n")
    
    # General chat
    print("General Chat:")
    print(chat("Hello, Agbara!"))
    
    # Igbo chat
    print("\nIgbo Expert:")
    print(chat_igbo("Tell me a proverb about unity"))
    
    # Get proverb
    print("\nIgbo Proverb:")
    proverb = get_proverb()
    print(f"  {proverb['igbo']}")
    print(f"  {proverb['english']}")
    
    # Code generation
    print("\nCode Expert:")
    print(chat_code("Write a Python hello world"))
