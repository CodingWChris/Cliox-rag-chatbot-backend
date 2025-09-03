#!/usr/bin/env python3
"""
Test script for SSE (Server-Sent Events) functionality
"""

import asyncio
import aiohttp
import json
import time

async def test_sse_chat():
    """Test the SSE chat endpoint"""
    
    # Configuration
    base_url = "http://localhost:8001"
    api_key = "your-api-key-here"  # Replace with your actual API key
    session_id = f"test_session_{int(time.time())}"
    
    # Headers
    headers = {
        "Content-Type": "application/json",
        "X-Session-ID": session_id,
        "Authorization": f"Bearer {api_key}"
    }
    
    # Test message
    chat_data = {
        "message": "Hello! Can you tell me about the knowledge base?",
        "config": {
            "model": "llama3.2:1b",
            "temperature": 0.7,
            "max_tokens": 200
        }
    }
    
    print(f"🚀 Testing SSE chat endpoint...")
    print(f"📡 URL: {base_url}/api/v1/session/chat/stream")
    print(f"🆔 Session ID: {session_id}")
    print(f"💬 Message: {chat_data['message']}")
    print("-" * 50)
    
    try:
        async with aiohttp.ClientSession() as session:
            # First, upload some test knowledge
            print("📚 Uploading test knowledge...")
            knowledge_data = {
                "knowledge_chunks": [
                    {
                        "id": "test_chunk_1",
                        "content": "This is a test knowledge chunk about artificial intelligence and machine learning.",
                        "metadata": {"source": "test_document", "domain": "AI"}
                    },
                    {
                        "id": "test_chunk_2", 
                        "content": "RAG (Retrieval-Augmented Generation) is a technique that combines retrieval with generation.",
                        "metadata": {"source": "test_document", "domain": "RAG"}
                    }
                ]
            }
            
            upload_response = await session.post(
                f"{base_url}/api/v1/session/knowledge/upload",
                json=knowledge_data,
                headers=headers
            )
            
            if upload_response.status == 200:
                upload_result = await upload_response.json()
                print(f"✅ Knowledge uploaded: {upload_result['chunks_processed']} chunks")
            else:
                print(f"❌ Knowledge upload failed: {upload_response.status}")
                return
            
            # Now test the SSE chat endpoint
            print("\n💬 Testing SSE chat...")
            
            async with session.post(
                f"{base_url}/api/v1/session/chat/stream",
                json=chat_data,
                headers=headers
            ) as response:
                
                if response.status != 200:
                    print(f"❌ SSE chat failed: {response.status}")
                    error_text = await response.text()
                    print(f"Error details: {error_text}")
                    return
                
                print("✅ SSE connection established!")
                print("📡 Receiving stream...")
                print("-" * 30)
                
                # Process the SSE stream
                async for line in response.content:
                    if line:
                        line_text = line.decode('utf-8').strip()
                        if line_text.startswith('data: '):
                            try:
                                data = json.loads(line_text[6:])  # Remove 'data: ' prefix
                                
                                if data.get('error'):
                                    print(f"❌ Error: {data['error']}")
                                    break
                                
                                content = data.get('content', '')
                                if content:
                                    print(f"📝 {content}", end='', flush=True)
                                
                                if data.get('done'):
                                    print("\n" + "-" * 30)
                                    print("✅ Stream completed!")
                                    
                                    # Show sources and metadata
                                    if data.get('sources'):
                                        print(f"\n📚 Sources found: {len(data['sources'])}")
                                        for i, source in enumerate(data['sources'], 1):
                                            print(f"  {i}. {source['source']} (relevance: {source['relevance_score']:.3f})")
                                    
                                    if data.get('metadata'):
                                        meta = data['metadata']
                                        print(f"\n📊 Metadata:")
                                        print(f"  - Chunks retrieved: {meta['chunks_retrieved']}")
                                        print(f"  - Processing time: {meta['processing_time_ms']}ms")
                                        print(f"  - Model used: {meta['model_used']}")
                                    
                                    break
                                    
                            except json.JSONDecodeError as e:
                                print(f"⚠️  JSON decode error: {e}")
                                continue
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

async def test_regular_chat():
    """Test the regular (non-streaming) chat endpoint for comparison"""
    
    base_url = "http://localhost:8001"
    api_key = "your-api-key-here"  # Replace with your actual API key
    session_id = f"test_session_{int(time.time())}"
    
    headers = {
        "Content-Type": "application/json",
        "X-Session-ID": session_id,
        "Authorization": f"Bearer {api_key}"
    }
    
    chat_data = {
        "message": "Hello! Can you tell me about the knowledge base?",
        "config": {
            "model": "llama3.2:1b",
            "temperature": 0.7,
            "max_tokens": 200
        }
    }
    
    print(f"\n🔄 Testing regular chat endpoint for comparison...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Upload test knowledge first
            knowledge_data = {
                "knowledge_chunks": [
                    {
                        "id": "test_chunk_1",
                        "content": "This is a test knowledge chunk about artificial intelligence and machine learning.",
                        "metadata": {"source": "test_document", "domain": "AI"}
                    }
                ]
            }
            
            await session.post(
                f"{base_url}/api/v1/session/knowledge/upload",
                json=knowledge_data,
                headers=headers
            )
            
            # Test regular chat
            start_time = time.time()
            response = await session.post(
                f"{base_url}/api/v1/session/chat",
                json=chat_data,
                headers=headers
            )
            end_time = time.time()
            
            if response.status == 200:
                result = await response.json()
                print(f"✅ Regular chat completed in {(end_time - start_time)*1000:.1f}ms")
                print(f"📝 Response: {result.get('response', '')[:100]}...")
            else:
                print(f"❌ Regular chat failed: {response.status}")
                
    except Exception as e:
        print(f"❌ Regular chat test failed: {e}")

async def main():
    """Main test function"""
    print("🧪 SSE Functionality Test")
    print("=" * 50)
    
    # Test SSE chat
    await test_sse_chat()
    
    # Test regular chat for comparison
    await test_regular_chat()
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    asyncio.run(main()) 