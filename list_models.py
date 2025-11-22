import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("GOOGLE_API_KEY not found in environment variables.")
else:
    try:
        client = genai.Client(api_key=api_key)
        print("Listing available models:")
        for m in client.models.list():
            print(f"- {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")
