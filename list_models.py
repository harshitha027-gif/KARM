import google.generativeai as genai
import sys

api_key = input("Paste your Gemini API key: ").strip()
genai.configure(api_key=api_key)

print("\nModels supporting generateContent:\n")
for m in genai.list_models():
    if "generateContent" in m.supported_generation_methods:
        print(f"  {m.name}")
