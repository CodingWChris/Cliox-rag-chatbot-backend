import aiohttp
import asyncio
import logging
from typing import Dict, Any, List, Optional
from ..config.settings import settings

logger = logging.getLogger(__name__)

class OllamaRequest:
    def __init__(
        self, 
        model: str, 
        prompt: str, 
        temperature: float = 0.7, 
        max_tokens: int = 500
    ):
        self.model = model
        self.prompt = prompt
        self.temperature = temperature
        self.max_tokens = max_tokens

class OllamaResponse:
    def __init__(self, response: str, model: str, done: bool = True):
        self.response = response
        self.model = model
        self.done = done

class OllamaService:
    def __init__(self):
        self.ollama_url = settings.ollama_url
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=120)
            )
        return self.session
    
    async def generate(self, request: OllamaRequest) -> OllamaResponse:
        """Generate response using Ollama API"""
        logger.info(f"🦙 Calling Ollama with model: {request.model}")
        
        session = await self._get_session()
        
        payload = {
            "model": request.model,
            "prompt": request.prompt,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_ctx": request.max_tokens,
                "top_k": 40,
                "top_p": 0.9
            }
        }
        
        try:
            async with session.post(
                f"{self.ollama_url}/api/generate",
                json=payload
            ) as response:
                if response.status != 200:
                    raise Exception(f"Ollama API error: {response.status}")
                
                data = await response.json()
                return OllamaResponse(
                    response=data.get("response", ""),
                    model=data.get("model", request.model),
                    done=data.get("done", True)
                )
        
        except Exception as e:
            logger.error(f"❌ Ollama generation error: {e}")
            raise
    
    async def list_models(self) -> List[str]:
        """List available Ollama models"""
        try:
            session = await self._get_session()
            async with session.get(f"{self.ollama_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    return [model.get("name", "") for model in data.get("models", [])]
                return []
        except Exception as e:
            logger.error(f"❌ Failed to list Ollama models: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check if Ollama is healthy"""
        try:
            session = await self._get_session()
            async with session.get(f"{self.ollama_url}/api/tags") as response:
                return response.status == 200
        except:
            return False
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

# Global ollama service instance
ollama_service = OllamaService() 