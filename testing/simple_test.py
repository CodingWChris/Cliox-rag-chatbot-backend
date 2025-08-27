#!/usr/bin/env python3
"""
Simple test script for vector service
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_vector_service():
    """Simple test for vector service"""
    
    print("🧪 Testing Vector Service")
    print("=" * 30)
    
    try:
        # Import the service
        from services.vector_service import vector_service
        print("✅ Vector service imported successfully")
        
        # Test basic functionality
        test_chunks = [
            {
                "id": "doc1",
                "content": "Machine learning is a subset of artificial intelligence.",
                "metadata": {"source": "ml.txt", "category": "technology"}
            },
            {
                "id": "doc2", 
                "content": "Deep learning uses neural networks for pattern recognition.",
                "metadata": {"source": "dl.txt", "category": "technology"}
            }
        ]
        
        # Convert to KnowledgeChunk objects
        from models.knowledge import KnowledgeChunk
        chunks = [
            KnowledgeChunk(**chunk) for chunk in test_chunks
        ]
        
        session_id = "test_session"
        
        # Test adding chunks
        print("📚 Adding chunks...")
        await vector_service.add_chunks(session_id, chunks)
        print("✅ Chunks added successfully")
        
        # Test search
        print("🔍 Testing search...")
        results = vector_service.search_similar(
            "What is machine learning?", 
            chunks, 
            top_k=2,
            session_id=session_id
        )
        
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. Similarity: {result.similarity:.3f} | Source: {result.metadata['source']}")
        
        # Clean up
        await vector_service.remove_session(session_id)
        print("✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_vector_service()) 