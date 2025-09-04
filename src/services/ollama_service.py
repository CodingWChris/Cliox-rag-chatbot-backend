import aiohttp
import asyncio
import logging
import json
from typing import Dict, Any, List, Optional, AsyncGenerator
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
                timeout=aiohttp.ClientTimeout(total=300)  
            )
        return self.session
    
    # ==============================================
    # LEGACY NON-STREAMING METHOD
    # ==============================================
    # Note: This method is kept for backward compatibility.
    # New implementations should use generate_stream() instead.
    
    async def generate(self, request: OllamaRequest) -> OllamaResponse:
        """
        LEGACY: Generate response using Ollama API (non-streaming)
        
        This is the non-streaming version kept for backward compatibility.
        For new implementations, use generate_stream() instead.
        """
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
            logger.info(f"📡 Sending request to {self.ollama_url}/api/generate")
            async with session.post(
                f"{self.ollama_url}/api/generate",
                json=payload
            ) as response:
                logger.info(f"📡 Received response with status: {response.status}")
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Ollama API error: {response.status} - {error_text}")
                
                data = await response.json()
                logger.info(f"✅ Ollama response received, length: {len(data.get('response', ''))}")
                
                return OllamaResponse(
                    response=data.get("response", ""),
                    model=data.get("model", request.model),
                    done=data.get("done", True)
                )
        
        except Exception as e:
            logger.error(f"❌ Ollama generation error: {e}")
            raise
    
    # ==============================================
    # STREAMING METHODS
    # ==============================================
    # These are the preferred methods for new implementations
    
    async def generate_stream(self, request: OllamaRequest) -> AsyncGenerator[str, None]:
        """
        Generate streaming response using Ollama API
        
        This is the preferred method for real-time response generation.
        Returns an async generator that yields text chunks as they're generated.
        """
        logger.info(f"🦙 [STREAM] Calling Ollama with model: {request.model}")
        
        session = await self._get_session()
        
        payload = {
            "model": request.model,
            "prompt": request.prompt,
            "stream": True,  # Enable streaming
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens
            }
        }
        
        try:
            async with session.post(
                f"{self.ollama_url}/api/generate",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"❌ Ollama streaming error: {response.status} - {error_text}")
                    raise Exception(f"Ollama error: {response.status}")
                
                # Process streaming response line by line
                async for line in response.content:
                    if line:
                        try:
                            # Parse JSON chunk
                            chunk_data = json.loads(line.decode('utf-8'))
                            
                            # Extract response text
                            if 'response' in chunk_data:
                                text_chunk = chunk_data['response']
                                if text_chunk:
                                    yield text_chunk
                            
                            # Check if done
                            if chunk_data.get('done', False):
                                logger.info(f"✅ [STREAM] Ollama streaming completed")
                                break
                                
                        except json.JSONDecodeError:
                            # Skip invalid JSON lines
                            continue
                            
        except Exception as e:
            logger.error(f"❌ Ollama streaming generation error: {e}")
            yield f"Error: {str(e)}"
    
    # ==============================================
    # UTILITY METHODS (SHARED)
    # ==============================================
    # These methods are used by both streaming and legacy implementations
    
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