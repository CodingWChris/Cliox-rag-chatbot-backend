#!/usr/bin/env python3
"""
Test SSE functionality without API key (since auth is disabled in development)
"""

import asyncio
import aiohttp
import json
import time

async def test_sse_no_auth():
    """Test SSE chat without authentication"""
    
    base_url = "http://localhost:8001"
    session_id = f"test_sse_no_auth_{int(time.time())}"
    
    # Headers without Authorization
    headers = {
        "Content-Type": "application/json",
        "X-Session-ID": session_id
    }
    
    print(f"🧪 Testing SSE without authentication...")
    print(f"📡 URL: {base_url}/api/v1/session/chat/stream")
    print(f"🆔 Session ID: {session_id}")
    print(f"🔓 No API key required (development mode)")
    print("-" * 50)
    
    try:
        async with aiohttp.ClientSession() as session:
            # 1. Upload test knowledge (no auth required)
            print("📚 Uploading test knowledge...")
            knowledge_data = {
                "knowledge_chunks": [
                    {
                        "id": "test_chunk_1",
                        "content": "Artificial Intelligence (AI) is a branch of computer science that aims to create intelligent machines that can perform tasks that typically require human intelligence.",
                        "metadata": {"source": "ai_textbook", "domain": "AI"}
                    },
                    {
                        "id": "test_chunk_2",
                        "content": "Machine Learning is a subset of AI that enables computers to learn and improve from experience without being explicitly programmed.",
                        "metadata": {"source": "ml_guide", "domain": "ML"}
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
                error_text = await upload_response.text()
                print(f"Error: {error_text}")
                return
            
            # 2. Test SSE chat endpoint
            print("\n💬 Testing SSE chat endpoint...")
            
            chat_data = {
                "message": "Hello! Can you explain what AI and Machine Learning are?",
                "config": {
                    "model": "llama3.2:1b",
                    "temperature": 0.7,
                    "max_tokens": 150
                }
            }
            
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
                full_response = ""
                chunk_count = 0
                
                async for line in response.content:
                    if line:
                        line_text = line.decode('utf-8').strip()
                        if line_text.startswith('data: '):
                            try:
                                data = json.loads(line_text[6:])  # Remove 'data: ' prefix
                                chunk_count += 1
                                
                                if data.get('error'):
                                    print(f"❌ Error: {data['error']}")
                                    break
                                
                                content = data.get('content', '')
                                if content:
                                    full_response += content
                                    print(f"📝 Chunk {chunk_count}: {content}", end='', flush=True)
                                
                                if data.get('done'):
                                    print("\n" + "-" * 30)
                                    print("✅ Stream completed!")
                                    print(f"📊 Total chunks received: {chunk_count}")
                                    print(f"📝 Full response length: {len(full_response)} characters")
                                    
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
                
                print(f"\n🎯 Final response: {full_response[:100]}...")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

async def test_regular_chat_no_auth():
    """Test regular chat without authentication for comparison"""
    
    base_url = "http://localhost:8001"
    session_id = f"test_regular_no_auth_{int(time.time())}"
    
    headers = {
        "Content-Type": "application/json",
        "X-Session-ID": session_id
    }
    
    print(f"\n🔄 Testing regular chat without authentication...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Upload test knowledge first
            knowledge_data = {
                "knowledge_chunks": [
                    {
                        "id": "test_chunk_1",
                        "content": "AI is a technology that enables machines to simulate human intelligence.",
                        "metadata": {"source": "test_doc", "domain": "AI"}
                    }
                ]
            }
            
            await session.post(
                f"{base_url}/api/v1/session/knowledge/upload",
                json=knowledge_data,
                headers=headers
            )
            
            # Test regular chat
            chat_data = {
                "message": "What is AI?",
                "config": {
                    "model": "llama3.2:1b",
                    "temperature": 0.7,
                    "max_tokens": 100
                }
            }
            
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
    print("🧪 SSE Functionality Test (No Authentication)")
    print("=" * 60)
    
    # Test SSE chat without auth
    await test_sse_no_auth()
    
    # Test regular chat without auth for comparison
    await test_regular_chat_no_auth()
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    asyncio.run(main()) 