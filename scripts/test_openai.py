from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if api_key:
    print("✅ OpenAI API key loaded successfully")
    print(f"Key starts with: {api_key[:20]}...")
else:
    print("❌ No OpenAI API key found")