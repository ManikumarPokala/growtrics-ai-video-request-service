import json
import httpx
from typing import Dict, Any
from app.core.config import settings, logger
from app.models.schemas import Storyboard
from app.storyboards.content_registry import get_fallback_storyboard
from app.core.interfaces import ILLMProvider

class OllamaLLMProvider(ILLMProvider):
    def __init__(self) -> None:
        self.endpoint = f"{settings.ollama_host.rstrip('/')}/api/generate"
        self.model = settings.ollama_model
        logger.info(f"OllamaLLMProvider initialized. Endpoint: {self.endpoint}, Model: {self.model}")

    async def generate_storyboard(self, query: str, retry_count: int = 0) -> Storyboard:
        """
        Request storyboard from Ollama, check Pydantic schemas, and run repair loops up to 3 times.
        Falls back to content_registry templates on persistent failure.
        """
        prompt = self._build_prompt(query)
        current_prompt = prompt
        
        for attempt in range(1, settings.max_retries + 1):
            logger.info(f"Ollama Storyboard Gen (Query: '{query}'): Attempt {attempt} of {settings.max_retries}")
            try:
                # Set a strict timeout to avoid hung request loops
                async with httpx.AsyncClient(timeout=10.0) as client:
                    payload = {
                        "model": self.model,
                        "prompt": current_prompt,
                        "stream": False,
                        "format": "json"
                    }
                    response = await client.post(self.endpoint, json=payload)
                    
                    if response.status_code != 200:
                        raise httpx.HTTPStatusError(
                            f"Ollama returned HTTP Status Code: {response.status_code}",
                            request=response.request,
                            response=response
                        )
                        
                    data = response.json()
                    raw_text = data.get("response", "").strip()
                    logger.info(f"Ollama response received for query '{query}': {raw_text[:200]}...")
                    
                    # Parse and validate with Pydantic Storyboard schema
                    storyboard = Storyboard.model_validate_json(raw_text)
                    
                    # Ensure total duration is under 30s limit
                    total_dur = sum(s.duration for s in storyboard.scenes)
                    if total_dur > 30.0:
                        # Normalize durations proportionally to fit inside 30 seconds
                        logger.warning(f"Generated storyboard total duration ({total_dur}s) exceeds 30s. Normalizing...")
                        for scene in storyboard.scenes:
                            scene.duration = (scene.duration / total_dur) * 30.0
                    
                    logger.info(f"Ollama Storyboard Gen success on attempt {attempt}.")
                    return storyboard
                    
            except Exception as e:
                logger.warning(f"Ollama parsing/connection failed on attempt {attempt}: {str(e)}")
                # If not the last attempt, build self-repair prompt with error context
                if attempt < settings.max_retries:
                    current_prompt = self._build_repair_prompt(prompt, current_prompt, str(e))
                else:
                    logger.error(f"Exceeded max Ollama repair retries for query: '{query}'. Loading fallback storyboard.")
                    
        # Load local predefined subject fallback storyboard
        return get_fallback_storyboard(query)

    def _build_prompt(self, query: str) -> str:
        return f"""You are an expert chemistry professor. Generate an educational video storyboard explaining the query: "{query}"

You MUST respond with a raw JSON object conforming EXACTLY to this schema:
{{
  "scenes": [
    {{
      "visual_type": "string",
      "script": "string",
      "duration": float
    }}
  ]
}}

Guidelines:
1. "scenes" must contain between 2 to 4 scenes.
2. "duration" must be in seconds, and the total duration of all scenes combined must be between 15.0 and 28.0 seconds.
3. "visual_type" must be one of the registered visualization types:
   - For pH scale questions: "ph_scale_overview", "acidic_solution", "basic_solution"
   - For Covalent bond questions: "atoms_intro", "electron_sharing", "molecule_formation"
   - For Ionic vs Covalent questions: "bond_comparison", "ionic_interaction", "covalent_interaction"
4. "script" is the spoken narration voiceover script for that scene.

Ensure your response is valid JSON and contains no other characters."""

    def _build_repair_prompt(self, original_prompt: str, last_response: str, error_message: str) -> str:
        return f"""{original_prompt}

Your previous response was invalid.
[Invalid Response]:
{last_response}

[Validation Error]:
{error_message}

Please fix the error and output valid JSON conforming exactly to the requested Pydantic schema."""

# Singleton provider instance
llm_provider = OllamaLLMProvider()
