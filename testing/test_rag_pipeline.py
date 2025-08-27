#!/usr/bin/env python3
"""
Debug script to test the RAG pipeline end-to-end
"""
import asyncio
import json
import logging
import aiohttp
import uuid

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8001"

async def test_pipeline():
    """Test the full RAG pipeline"""
    
    async with aiohttp.ClientSession() as http_session:
        try:
            # 1. Generate a session ID
            session_id = str(uuid.uuid4())
            logger.info(f"🚀 Using session ID: {session_id}")
            
            # 2. Upload test knowledge
            logger.info("📚 Uploading test knowledge...")
            test_content = """This is a test document about machine learning.

Machine Learning Basics:
- Machine learning is a subset of artificial intelligence (AI)
- It involves training algorithms to make predictions or decisions
- Common types include supervised, unsupervised, and reinforcement learning
- Popular algorithms include linear regression, decision trees, and neural networks

Deep Learning:
- Deep learning is a subset of machine learning
- It uses neural networks with multiple layers
- It's particularly effective for image recognition and natural language processing
- Popular frameworks include TensorFlow and PyTorch

Applications:
- Image recognition and computer vision
- Natural language processing and chatbots
- Recommendation systems
- Autonomous vehicles
- Medical diagnosis"""

            # Split content into chunks (simulating the frontend processing)
            import re
            paragraphs = [p.strip() for p in test_content.split('\n\n') if p.strip()]
            
            knowledge_chunks = []
            for i, paragraph in enumerate(paragraphs):
                chunk_id = f"chunk_{session_id}_{i}"
                knowledge_chunks.append({
                    "id": chunk_id,
                    "content": paragraph,
                    "metadata": {
                        "source": "test_document.txt",
                        "author": "Test User",
                        "topic": "Machine Learning",
                        "chunk_index": i
                    }
                })

            knowledge_data = {
                "knowledge_chunks": knowledge_chunks
            }

            headers = {"X-Session-ID": session_id}

            async with http_session.post(
                f"{BASE_URL}/api/v1/session/knowledge/upload",
                json=knowledge_data,
                headers=headers
            ) as resp:
                if resp.status != 200:
                    logger.error(f"Failed to upload knowledge: {resp.status}")
                    logger.error(await resp.text())
                    return
                
                upload_result = await resp.json()
                logger.info(f"✅ Uploaded knowledge: {upload_result}")
            
            # 3. Wait a moment for processing
            await asyncio.sleep(1)
            
            # 4. Test different types of questions
            test_questions = [
                "What is machine learning?",
                "Tell me about deep learning",
                "What are some applications of machine learning?",
                "How does neural networks work?",
                "What is the difference between supervised and unsupervised learning?"
            ]
            
            for question in test_questions:
                logger.info(f"\n❓ Testing question: '{question}'")
                
                chat_data = {
                    "message": question,
                    "config": {
                        "model": "llama3.1:8b",
                        "temperature": 0.7,
                        "top_k": 3
                    }
                }
                
                async with http_session.post(
                    f"{BASE_URL}/api/v1/session/chat",
                    json=chat_data,
                    headers=headers
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"Failed to send chat: {resp.status}")
                        logger.error(await resp.text())
                        continue
                    
                    response = await resp.json()
                    logger.info(f"🤖 Response: {response.get('response', 'No response')}")
                    logger.info(f"📄 Sources found: {len(response.get('sources', []))}")
                    logger.info(f"📊 Chunks retrieved: {response.get('metadata', {}).get('chunks_retrieved', 0)}")
                    
                    if response.get('sources'):
                        for i, source in enumerate(response['sources'], 1):
                            logger.info(f"  Source {i}: {source.get('source')} (relevance: {source.get('relevance_score', 'N/A')})")
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pipeline())
