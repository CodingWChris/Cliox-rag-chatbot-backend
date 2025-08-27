#!/usr/bin/env python3
"""
Test script to verify query embedding process
"""

import asyncio
import sys
import os
import logging

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging to see debug messages
logging.basicConfig(level=logging.DEBUG)

from models.knowledge import KnowledgeChunk
from services.vector_service import vector_service

async def test_embedding_verification():
    """Test and verify the embedding process"""
    
    print("🧪 Testing Query Embedding Verification")
    print("=" * 50)
    
    # Test data
    test_chunks = [
        KnowledgeChunk(
            id="doc1",
            content="Machine learning is a subset of artificial intelligence.",
            metadata={"source": "ml.txt", "category": "technology"}
        ),
        KnowledgeChunk(
            id="doc2", 
            content="Deep learning uses neural networks for pattern recognition.",
            metadata={"source": "dl.txt", "category": "technology"}
        )
    ]
    
    test_queries = [
        "What is machine learning?",
        "How does deep learning work?",
        "Tell me about neural networks",
        "What is AI?",
        "   spaced query   "  # Test whitespace handling
    ]
    
    session_id = "test_embedding_session"
    
    try:
        # 1. Add chunks to vector store
        print("📚 Adding test chunks...")
        await vector_service.add_chunks(session_id, test_chunks)
        print("✅ Chunks added successfully")
        
        # 2. Test query preprocessing
        print("\n🔍 Testing query preprocessing...")
        for query in test_queries:
            processed = vector_service._preprocess_query(query)
            print(f"Original: '{query}'")
            print(f"Processed: '{processed}'")
            print(f"Length: {len(processed)}")
            print("-" * 30)
        
        # 3. Test embedding generation
        print("\n🔍 Testing embedding generation...")
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            
            # Test with pre-computed embeddings
            results_knn = vector_service.search_similar(
                query, 
                test_chunks, 
                top_k=2,
                session_id=session_id
            )
            
            print(f"KNN Results: {len(results_knn)} chunks found")
            for i, result in enumerate(results_knn, 1):
                print(f"  {i}. Similarity: {result.similarity:.3f} | Source: {result.metadata['source']}")
            
            # Test on-the-fly search
            results_otf = vector_service.search_similar(
                query, 
                test_chunks, 
                top_k=2,
                session_id=None  # Force on-the-fly search
            )
            
            print(f"On-the-fly Results: {len(results_otf)} chunks found")
            for i, result in enumerate(results_otf, 1):
                print(f"  {i}. Similarity: {result.similarity:.3f} | Source: {result.metadata['source']}")
        
        # 4. Test embedding consistency
        print("\n🔍 Testing embedding consistency...")
        query = "machine learning"
        
        # Test multiple calls to ensure consistency
        results1 = vector_service.search_similar(query, test_chunks, top_k=1, session_id=session_id)
        results2 = vector_service.search_similar(query, test_chunks, top_k=1, session_id=session_id)
        
        if results1 and results2:
            similarity1 = results1[0].similarity
            similarity2 = results2[0].similarity
            print(f"First call similarity: {similarity1:.6f}")
            print(f"Second call similarity: {similarity2:.6f}")
            print(f"Consistent: {abs(similarity1 - similarity2) < 1e-6}")
        
        # 5. Clean up
        print(f"\n🧹 Cleaning up...")
        await vector_service.remove_session(session_id)
        print("✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_embedding_verification()) 