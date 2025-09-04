import time
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, AsyncGenerator
from ..models.knowledge import ChatResponse, ChatSource, ChatMetadata, StreamChunk
from .session_service import session_service
from .ollama_service import ollama_service, OllamaRequest
from .vector_service import vector_service
from .s3_conversation_service import conversation_storage, ConversationMessage
from .conversation_summarizer import conversation_summarizer
from ..config.settings import settings

logger = logging.getLogger(__name__)

class RAGService:
    # ==============================================
    # LEGACY NON-STREAMING METHODS
    # ==============================================
    # Note: These methods are kept for backward compatibility.
    # New implementations should use the streaming versions above.
    # Use ?stream=false in the API to access these legacy methods.
    
    async def process_chat(
        self, 
        session_id: str, 
        message: str, 
        config: Dict[str, Any]
    ) -> ChatResponse:
        """
        LEGACY: Process chat message using RAG pipeline with conversation context
        
        This is the non-streaming version kept for backward compatibility.
        For new implementations, use process_chat_stream() instead.
        """
        start_time = time.time()
        
        try:
            # 0. Save user message to conversation history
            user_message = ConversationMessage(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                role="user",
                content=message,
                timestamp=datetime.now(timezone.utc).isoformat(),
                metadata={"config": config}
            )
            await conversation_storage.save_message(session_id, user_message)
            
            # 1. Get conversation context (summary + recent messages)
            conversation_context = await conversation_summarizer.get_conversation_context(
                session_id, 
                max_tokens=settings.conversation_context_max_tokens
            )
            
            # 2. Get session knowledge
            knowledge = await session_service.get_knowledge(session_id)
            
            logger.info(f"🔍 Processing chat for session {session_id}: \"{message}\"")
            
            if not knowledge:
                # Fallback to general LLM without RAG (but with conversation context)
                logger.info("📝 No knowledge base found - using general LLM mode with conversation context")
                prompt = self._build_general_prompt_with_context(message, conversation_context)
                relevant_chunks = []
            else:
                # Use RAG with knowledge base and conversation context
                logger.info(f"📚 Using knowledge base with {len(knowledge.chunks)} chunks")
                
                # 3. Search for relevant chunks using semantic search
                logger.info(f"🔍 Searching for relevant chunks with query: '{message}'")
                relevant_chunks = vector_service.search_similar(
                    message, 
                    knowledge.chunks, 
                    config.get("top_k", 3),
                    session_id  # Pass session_id for optimized search
                )
                
                logger.info(f"📄 Found {len(relevant_chunks)} relevant chunks")
                if relevant_chunks:
                    for i, chunk in enumerate(relevant_chunks, 1):
                        logger.info(f"  {i}. Similarity: {chunk.similarity:.3f} | Source: {chunk.metadata.get('source', 'Unknown')}")
                
                # 4. Check if any relevant chunks were found
                if len(relevant_chunks) == 0:
                    # No relevant chunks found - fall back to general mode with context
                    logger.info("🔄 No relevant chunks found - falling back to general LLM mode with conversation context")
                    prompt = self._build_general_prompt_with_context(message, conversation_context)
                else:
                    # Build RAG prompt with knowledge context and conversation context
                    knowledge_context = self._build_context(relevant_chunks)
                    prompt = self._build_rag_prompt_with_context(knowledge_context, message, conversation_context)
            
            # 5. Call Ollama
            ollama_request = OllamaRequest(
                model=config.get("model", settings.default_model),
                prompt=prompt,
                temperature=config.get("temperature", 0.7),
                max_tokens=config.get("max_tokens", 500)
            )
            
            llm_response = await ollama_service.generate(ollama_request)
            
            processing_time = int((time.time() - start_time) * 1000)
            logger.info(f"🤖 Generated response in {processing_time}ms")
            
            # 6. Save assistant response to conversation history
            assistant_message = ConversationMessage(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                role="assistant", 
                content=llm_response.response,
                timestamp=datetime.now(timezone.utc).isoformat(),
                metadata={
                    "model": llm_response.model,
                    "processing_time_ms": processing_time,
                    "chunks_used": len(relevant_chunks),
                    "sources": [chunk.metadata.get("source", "Unknown") for chunk in relevant_chunks]
                }
            )
            await conversation_storage.save_message(session_id, assistant_message)
            
            # 7. Check if we need to update conversation summary
            should_summarize = await conversation_summarizer.should_update_summary(session_id)
            if should_summarize:
                logger.info(f"📊 Triggering summary update for session {session_id}")
                # Run summarization in background (don't wait for it)
                import asyncio
                asyncio.create_task(conversation_summarizer.generate_summary(session_id))
            
            # 8. Build response
            sources = [
                ChatSource(
                    source=chunk.metadata.get("source", "Unknown"),
                    relevance_score=chunk.score,
                    content_preview=chunk.content[:100] + "..." if len(chunk.content) > 100 else chunk.content
                )
                for chunk in relevant_chunks
            ]
            
            response = ChatResponse(
                success=True,
                response=llm_response.response,
                sources=sources,
                metadata=ChatMetadata(
                    chunks_retrieved=len(relevant_chunks),
                    processing_time_ms=processing_time,
                    model_used=llm_response.model
                )
            )
            
            logger.info(f"✅ Chat processing completed for session {session_id}")
            return response
        
        except Exception as e:
            logger.error(f"❌ Chat processing error for session {session_id}: {e}")
            return ChatResponse(
                success=False,
                error="processing_error",
                message=str(e)
            )
    
    # ==============================================
    # STREAMING METHODS  
    # ==============================================
    # These are the preferred methods for new implementations.
    # They provide real-time response generation with progress updates.
    
    async def process_chat_stream(
        self, 
        session_id: str, 
        message: str, 
        config: Dict[str, Any]
    ) -> AsyncGenerator[StreamChunk, None]:
        """Process chat message using RAG pipeline with streaming response"""
        start_time = time.time()
        
        try:
            # Yield initial status
            yield StreamChunk(type="status", content="Processing your request...")
            
            # Same logic as process_chat but with streaming
            user_message = ConversationMessage(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                role="user",
                content=message,
                timestamp=datetime.now(timezone.utc).isoformat(),
                metadata={"config": config}
            )
            await conversation_storage.save_message(session_id, user_message)
            
            # Get conversation context and knowledge
            conversation_context = await conversation_summarizer.get_conversation_context(
                session_id, 
                max_tokens=settings.conversation_context_max_tokens
            )
            knowledge = await session_service.get_knowledge(session_id)
            
            yield StreamChunk(type="status", content="Searching knowledge base...")
            
            # Same RAG logic
            if not knowledge:
                prompt = self._build_general_prompt_with_context(message, conversation_context)
                relevant_chunks = []
                sources = []
            else:
                relevant_chunks = vector_service.search_similar(
                    message, 
                    knowledge.chunks, 
                    config.get("top_k", 3),
                    session_id
                )
                
                if len(relevant_chunks) == 0:
                    prompt = self._build_general_prompt_with_context(message, conversation_context)
                    sources = []
                else:
                    knowledge_context = self._build_context(relevant_chunks)
                    prompt = self._build_rag_prompt_with_context(knowledge_context, message, conversation_context)
                    sources = [ChatSource(
                        source=chunk.metadata.get("source", "Unknown"),
                        relevance_score=chunk.similarity,
                        content_preview=chunk.content[:100] + "..."
                    ) for chunk in relevant_chunks]
            
            yield StreamChunk(type="status", content="Generating response...", sources=sources)
            
            # Stream response from Ollama
            ollama_request = OllamaRequest(
                model=config.get("model", settings.default_model),
                prompt=prompt,
                temperature=config.get("temperature", 0.7),
                max_tokens=config.get("max_tokens", 500)
            )
            
            full_response = ""
            async for chunk in ollama_service.generate_stream(ollama_request):
                if chunk and chunk.strip():
                    full_response += chunk
                    yield StreamChunk(
                        type="chunk", 
                        content=chunk,
                        sources=sources,
                        metadata={"session_id": session_id}
                    )
            
            # Save assistant response
            assistant_message = ConversationMessage(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                role="assistant", 
                content=full_response,
                timestamp=datetime.now(timezone.utc).isoformat(),
                metadata={
                    "sources": [s.source for s in sources] if sources else [],
                    "model": config.get("model", settings.default_model),
                    "processing_time_ms": int((time.time() - start_time) * 1000)
                }
            )
            await conversation_storage.save_message(session_id, assistant_message)
            
            # Final completion chunk
            yield StreamChunk(
                type="complete", 
                content="Response finished",
                metadata={"total_response_length": len(full_response)}
            )
            
        except Exception as e:
            logger.error(f"❌ Streaming chat processing error for session {session_id}: {e}")
            yield StreamChunk(type="error", content=f"Error: {str(e)}")
    
    def _build_context(self, chunks) -> str:
        """Build context string from relevant chunks"""
        context_parts = []
        for chunk in chunks:
            source = chunk.metadata.get("source", "Unknown")
            context_parts.append(f"[Source: {source}]\n{chunk.content}")
        return "\n\n---\n\n".join(context_parts)
    
    def _build_rag_prompt_with_context(self, knowledge_context: str, message: str, conversation_context: str) -> str:
        """Build RAG prompt with both knowledge base and conversation context"""
        prompt_parts = ["You are a helpful AI assistant."]
        
        if conversation_context:
            prompt_parts.append(f"Conversation context:\n{conversation_context}")
        
        prompt_parts.append(f"Relevant knowledge base information:\n{knowledge_context}")
        
        prompt_parts.append(f"Current question: {message}")
        
        prompt_parts.append("""Please provide a comprehensive answer that:
            1. Uses the knowledge base information as your primary source
            2. Considers the conversation context and history 
            3. Maintains continuity with previous exchanges
            4. Cites sources when using knowledge base information

            Answer:""")
        
        return "\n\n".join(prompt_parts)
    
    def _build_general_prompt_with_context(self, message: str, conversation_context: str) -> str:
        """Build general prompt with conversation context (no knowledge base)"""
        prompt_parts = ["You are a helpful AI assistant."]
        
        if conversation_context:
            prompt_parts.append(f"Conversation context:\n{conversation_context}")
        
        prompt_parts.append(f"Current question: {message}")
        
        prompt_parts.append("""Please provide a clear and informative answer that:
            1. Considers the conversation context and history
            2. Maintains continuity with previous exchanges
            3. Builds on what has been discussed before

            Answer:""")
        
        return "\n\n".join(prompt_parts)
    
    # ==============================================
    # LEGACY HELPER METHODS
    # ==============================================
    # Note: These methods are kept for backward compatibility with the
    # non-streaming process_chat() method. They are not used by the 
    # streaming implementation which has more optimized prompt building.
    
    def _build_rag_prompt(self, context: str, message: str) -> str:
        """
        LEGACY: Build RAG prompt for LLM - used when relevant chunks are found
        
        This is the legacy version without conversation context.
        New streaming implementation uses _build_rag_prompt_with_context() instead.
        """
        return f"""You are a helpful AI assistant. Based on the following relevant knowledge base information:

        {context}

        Question: {message}

        Please provide a comprehensive answer using the knowledge base information above as your primary source, and enhance it with your general knowledge where appropriate. Always cite the sources when using information from the knowledge base.

        Answer:"""

    def _build_general_prompt(self, message: str) -> str:
        """
        LEGACY: Build general prompt for LLM without RAG context
        
        This is the legacy version without conversation context.
        New streaming implementation uses _build_general_prompt_with_context() instead.
        """
        return f"""You are a helpful AI assistant. Please provide a clear and informative answer to the following question:

        Question: {message}

        Answer:"""

# Global RAG service instance
rag_service = RAGService() 