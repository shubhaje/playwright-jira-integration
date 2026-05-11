#Local llama3/mistral
import json
import requests
from config.settings import OLLAMA_URL, OLLAMA_MODEL
from ai_engine.base_engine import BaseEngine

class OllamaEngine(BaseEngine):

    def __init__(self):
        self.url   = f"{OLLAMA_URL}/api/generate"
        self.model = OLLAMA_MODEL
        self._check_connection()

    def _check_connection(self):
        try:
            r      = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            models = [m["name"] for m in r.json().get("models", [])]
            match  = any(self.model in m for m in models)
            if not match:
                print(f"⚠️  Model '{self.model}' not pulled yet.")
                print(f"   Run: ollama pull {self.model}")
            else:
                print(f"✅ Ollama engine ready ({self.model})")
        except requests.exceptions.ConnectionError:
            print(f"❌ Ollama not running. Start it with: ollama serve")
        except Exception as e:
            print(f"❌ Ollama check failed: {e}")

    def generate_scenarios(self, jira_story: dict, page_context: dict) -> list[dict]:
        prompt = self._build_prompt(jira_story, page_context)
        try:
            print(f"🤖 Ollama ({self.model}) generating scenarios...")
            response = requests.post(self.url, json={
                "model":  self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,    # consistent JSON output
                    "num_predict": 2048    # max tokens
                }
            }, timeout=180)              # local models can be slow first run
            response.raise_for_status()
            raw_text  = response.json().get("response", "").strip()
            scenarios = self._parse(raw_text)
            print(f"✅ Generated {len(scenarios)} scenarios")
            return scenarios
        except requests.exceptions.ConnectionError:
            print("❌ Ollama not running. Run: ollama serve")
            return []
        except Exception as e:
            print(f"❌ Ollama generation failed: {e}")
            return []

    def _parse(self, text: str) -> list[dict]:
        text = text.strip()
        # Extract JSON array from anywhere in the response
        start = text.find("[")
        end   = text.rfind("]") + 1
        if start != -1 and end > start:
            text = text[start:end]
        try:
            result = json.loads(text)
            if isinstance(result, list):
                return result
            return []
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
            print(f"   Raw preview: {text[:300]}")
            return []