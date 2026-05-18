from config.settings import AI_ENGINE

def get_engine():
    if AI_ENGINE == "ollama":
        from ai_engine.ollama_engine import OllamaEngine
        return OllamaEngine()
    else:
        from ai_engine.gemini_engine import GeminiEngine
        return GeminiEngine()