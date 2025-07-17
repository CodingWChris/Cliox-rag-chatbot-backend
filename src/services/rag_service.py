import time
import logging
from typing import Dict, Any
from ..models.knowledge import ChatResponse, ChatSource, ChatMetadata
from .session_service import session_service
from .ollama_service import ollama_service, OllamaRequest
from .vector_service import vector_service
from ..config.settings import settings

logger = logging.getLogger(__name__)

class RAGService:
    async def process_chat(
        self, 
        session_id: str, 
        message: str, 
        config: Dict[str, Any]
    ) -> ChatResponse:
        """Process chat message using RAG pipeline"""
        start_time = time.time()
        
        try:
            # 1. Get session knowledge
            knowledge = await session_service.get_knowledge(session_id)
            
            logger.info(f"🔍 Processing chat for session {session_id}: \"{message}\"")
            
            if not knowledge:
                # Fallback to general LLM without RAG
                logger.info("📝 No knowledge base found - using general LLM mode")
                prompt = self._build_general_prompt(message)
                relevant_chunks = []
            else:
                # Use RAG with knowledge base
                logger.info(f"📚 Using knowledge base with {len(knowledge.chunks)} chunks")
                
                # 2. Search for relevant chunks
                relevant_chunks = vector_service.search_similar(
                    message, 
                    knowledge.chunks, 
                    config.get("top_k", 3)
                )
                
                logger.info(f"📄 Found {len(relevant_chunks)} relevant chunks")
                
                # 3. Check if any relevant chunks were found
                if len(relevant_chunks) == 0:
                    # No relevant chunks found - fall back to general mode
                    logger.info("🔄 No relevant chunks found - falling back to general LLM mode")
                    prompt = self._build_general_prompt(message)
                else:
                    # Build RAG prompt with context
                    context = self._build_context(relevant_chunks)
                    prompt = self._build_rag_prompt(context, message)
            
            # 4. Call Ollama
            ollama_request = OllamaRequest(
                model=config.get("model", settings.default_model),
                prompt=prompt,
                temperature=config.get("temperature", 0.7),
                max_tokens=config.get("max_tokens", 500)
            )
            
            llm_response = await ollama_service.generate(ollama_request)
            
            processing_time = int((time.time() - start_time) * 1000)
            logger.info(f"🤖 Generated response in {processing_time}ms")
            
            # 5. Build response
            sources = [
                ChatSource(
                    source=chunk.metadata.get("source", "Unknown"),
                    relevance_score=chunk.score,
                    content_preview=chunk.content[:100] + "..." if len(chunk.content) > 100 else chunk.content
                )
                for chunk in relevant_chunks
            ]
            
            return ChatResponse(
                success=True,
                response=llm_response.response,
                sources=sources,
                metadata=ChatMetadata(
                    chunks_retrieved=len(relevant_chunks),
                    processing_time_ms=processing_time,
                    model_used=llm_response.model
                )
            )
        
        except Exception as e:
            logger.error(f"❌ Chat processing error for session {session_id}: {e}")
            return ChatResponse(
                success=False,
                error="processing_error",
                message=str(e)
            )
    
    def _build_context(self, chunks) -> str:
        """Build context string from relevant chunks"""
        context_parts = []
        for chunk in chunks:
            source = chunk.metadata.get("source", "Unknown")
            context_parts.append(f"[Source: {source}]\n{chunk.content}")
        return "\n\n---\n\n".join(context_parts)
    
    def _build_rag_prompt(self, context: str, message: str) -> str:
        """Build RAG prompt for LLM - used when relevant chunks are found"""
        return f"""You are a helpful AI assistant. Based on the following relevant knowledge base information:

{context}

Question: {message}

Please provide a comprehensive answer using the knowledge base information above as your primary source, and enhance it with your general knowledge where appropriate. Always cite the sources when using information from the knowledge base.

Answer:"""

    def _build_general_prompt(self, message: str) -> str:
        """Build general prompt for LLM without RAG context"""
        return f"""You are a helpful AI assistant. Please provide a clear and informative answer to the following question:

Question: {message}

Answer:"""

# Global RAG service instance
rag_service = RAGService() 