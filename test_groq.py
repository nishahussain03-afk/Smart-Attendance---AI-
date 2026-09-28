import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise RuntimeError("HF_TOKEN is missing from .env")

client = InferenceClient(
    api_key=HF_TOKEN,
    provider="groq"
)

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "system",
            "content": "You are a helpful AI assistant for a college attendance management system."
        },
        {
            "role": "user",
            "content": "Say hello and explain in one sentence what an attendance management system does."
        }
    ],
    max_tokens=100
)

print()
print("=" * 60)
print("HUGGING FACE + GROQ TEST")
print("=" * 60)
print()
print(response.choices[0].message.content)
print()
print("API TEST: SUCCESS")