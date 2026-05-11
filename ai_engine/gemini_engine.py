import json
import time
from google import genai
from google.genai import types
from config.settings import GOOGLE_API_KEY
from ai_engine.base_engine import BaseEngine

class GeminiEngine(BaseEngine):

    MODELS = [
        "gemini-1.5-flash-8b",   # try first — separate quota
        "gemini-1.5-flash",
        "gemini-2.0-flash",
    ]

    def __init__(self):
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is missing in config/.env")
        self.client = genai.Client(api_key=GOOGLE_API_KEY)
        self.model  = self._find_available_model()

    def _find_available_model(self):
        """Try each model until one responds without quota error."""
        for model in self.MODELS:
            try:
                self.client.models.generate_content(
                    model=model,
                    contents="hello",
                    config=types.GenerateContentConfig(max_output_tokens=5)
                )
                print(f"✅ Gemini engine ready ({model})")
                return model
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    print(f"⚠️  {model} quota exhausted, trying next...")
                    time.sleep(2)
                else:
                    print(f"⚠️  {model} error: {e}")
        print("❌ All Gemini models quota exhausted. Switch AI_ENGINE=ollama in .env")
        return self.MODELS[0]

    def generate_scenarios(self, jira_story: dict, page_context: dict) -> list[dict]:
        prompt = self._build_prompt(jira_story, page_context)
        for attempt in range(3):
            try:
                print(f"🤖 Gemini ({self.model}) generating scenarios...")
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        max_output_tokens=2048,
                        temperature=0.3,
                    )
                )
                scenarios = self._parse(response.text.strip())
                print(f"✅ Generated {len(scenarios)} scenarios")
                return scenarios
            except Exception as e:
                if "429" in str(e):
                    wait = 60 * (attempt + 1)
                    print(f"⚠️  Rate limit hit. Waiting {wait}s... (attempt {attempt+1}/3)")
                    time.sleep(wait)
                else:
                    print(f"❌ Gemini failed: {e}")
                    return []
        print("❌ All retries exhausted.")
        return []

    def _parse(self, text: str) -> list[dict]:
        text  = text.strip()
        start = text.find("[")
        end   = text.rfind("]") + 1
        if start != -1 and end > start:
            text = text[start:end]
        try:
            result = json.loads(text)
            return result if isinstance(result, list) else []
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
            print(f"   Raw preview: {text[:300]}")
            return []