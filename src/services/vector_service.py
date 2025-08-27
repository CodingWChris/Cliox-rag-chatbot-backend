import logging
import uuid
import tempfile
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from ..models.knowledge import KnowledgeChunk

logger = logging.getLogger(__name__)

class RelevantChunk:
    def __init__(self, chunk: KnowledgeChunk, score: float = 0.0, similarity: float = 0.0):
        self.id = chunk.id
        self.content = chunk.content
        self.metadata = chunk.metadata
        self.score = score
        self.similarity = similarity

class VectorService:
    def __init__(self):
        """Initialize the vector service with ChromaDB and all-MiniLM-L6-v2 model"""
        logger.info("🚀 Initializing Vector Service with ChromaDB and all-MiniLM-L6-v2")
        
        # Load the sentence transformer model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB client with in-memory storage (ephemeral)
        # This ensures data is not persisted across application restarts
        self.chroma_client = chromadb.Client(Settings(
            is_persistent=False,  # Use in-memory storage
            anonymized_telemetry=False
        ))
        
        # Track active sessions and their collections
        self.session_collections: Dict[str, str] = {}  # session_id -> collection_name
        
        logger.info("✅ Vector Service initialized successfully with ChromaDB")
    
    def _get_text_for_embedding(self, chunk: KnowledgeChunk) -> str:
        """Combine chunk content and metadata for embedding"""
        content = chunk.content
        
        # Include metadata if available
        if chunk.metadata:
            metadata_text = " ".join(str(v) for v in chunk.metadata.values())
            combined_text = f"{content} {metadata_text}"
        else:
            combined_text = content
            
        return combined_text
    
    def _preprocess_query(self, query: str) -> str:
        """Preprocess query text for embedding"""
        # Basic preprocessing - can be extended with more sophisticated text cleaning
        # For now, just ensure consistent formatting
        return query.strip()
    
    def _get_collection_name(self, session_id: str) -> str:
        """Generate a unique collection name for a session"""
        if session_id not in self.session_collections:
            # Create a unique collection name for this session
            collection_name = f"session_{session_id}_{uuid.uuid4().hex[:8]}"
            self.session_collections[session_id] = collection_name
        return self.session_collections[session_id]
    
    async def add_chunks(self, session_id: str, chunks: List[KnowledgeChunk]) -> None:
        """Add chunks to ChromaDB collection for the session"""
        logger.info(f"📚 Adding {len(chunks)} chunks to ChromaDB for session {session_id}")
        
        if not chunks:
            return
        
        try:
            # Get or create collection for this session
            collection_name = self._get_collection_name(session_id)
            
            # Create collection (or get existing one)
            collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"session_id": session_id}
            )
            
            # Prepare data for ChromaDB
            documents = []
            metadatas = []
            ids = []
            
            for chunk in chunks:
                documents.append(self._get_text_for_embedding(chunk))
                
                # Preprocess metadata to ensure ChromaDB compatibility
                processed_metadata = {}
                if chunk.metadata:
                    for key, value in chunk.metadata.items():
                        if isinstance(value, list):
                            # Convert lists to comma-separated strings
                            processed_metadata[key] = ", ".join(str(item) for item in value)
                        elif isinstance(value, (str, int, float, bool)):
                            processed_metadata[key] = value
                        else:
                            # Convert other types to strings
                            processed_metadata[key] = str(value)
                
                metadatas.append({
                    **processed_metadata,
                    "chunk_id": chunk.id,
                    "content": chunk.content  # Store original content in metadata
                })
                ids.append(chunk.id)
            
            # Add documents to collection
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"✅ Added {len(chunks)} chunks to ChromaDB collection '{collection_name}'")
            
        except Exception as e:
            logger.error(f"❌ Error adding chunks to ChromaDB: {e}")
            raise
    
    def search_similar(
        self, 
        query: str, 
        chunks: List[KnowledgeChunk], 
        top_k: int = 3,
        session_id: Optional[str] = None
    ) -> List[RelevantChunk]:
        """
        Search for similar chunks using ChromaDB
        """
        if not chunks:
            return []
        
        # If we have a session_id and collection, use ChromaDB search
        if session_id and session_id in self.session_collections:
            return self._search_with_chromadb(query, session_id, top_k)
        
        # Otherwise, compute embeddings on-the-fly (fallback)
        return self._search_on_the_fly(query, chunks, top_k)
    
    def _search_with_chromadb(self, query: str, session_id: str, top_k: int) -> List[RelevantChunk]:
        """Search using ChromaDB collection"""
        try:
            collection_name = self.session_collections[session_id]
            collection = self.chroma_client.get_collection(name=collection_name)
            
            # Preprocess and search
            processed_query = self._preprocess_query(query)
            logger.debug(f"🔍 Query preprocessing: '{query}' -> '{processed_query}'")
            
            # Query ChromaDB
            results = collection.query(
                query_texts=[processed_query],
                n_results=min(top_k, collection.count())
            )
            
            # Build response
            relevant_chunks = []
            if results['ids'] and results['ids'][0]:
                for i, (chunk_id, distance, metadata) in enumerate(zip(
                    results['ids'][0],
                    results['distances'][0],
                    results['metadatas'][0]
                )):
                    # Convert distance to similarity (ChromaDB returns distance, we want similarity)
                    similarity = 1.0 - distance
                    
                    # Reconstruct KnowledgeChunk from metadata
                    chunk_metadata = {k: v for k, v in metadata.items() 
                                    if k not in ['chunk_id', 'content']}
                    
                    chunk = KnowledgeChunk(
                        id=metadata['chunk_id'],
                        content=metadata['content'],
                        metadata=chunk_metadata
                    )
                    
                    relevant_chunks.append(RelevantChunk(
                        chunk=chunk,
                        score=float(similarity),
                        similarity=float(similarity)
                    ))
            
            logger.info(f"🔍 Found {len(relevant_chunks)} similar chunks using ChromaDB")
            return relevant_chunks
            
        except Exception as e:
            logger.error(f"❌ Error in ChromaDB search: {e}")
            return []
    
    def _search_on_the_fly(self, query: str, chunks: List[KnowledgeChunk], top_k: int) -> List[RelevantChunk]:
        """Search by computing embeddings on-the-fly (fallback)"""
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            
            # Prepare texts - ensure consistent preprocessing
            chunk_texts = [self._get_text_for_embedding(chunk) for chunk in chunks]
            
            # Encode query and chunks separately for better control
            processed_query = self._preprocess_query(query)
            logger.debug(f"🔍 Query preprocessing: '{query}' -> '{processed_query}'")
            query_embedding = self.model.encode([processed_query])
            chunk_embeddings = self.model.encode(chunk_texts)
            logger.debug(f"🔍 Query embedding shape: {query_embedding.shape}, Chunk embeddings shape: {chunk_embeddings.shape}")
            
            # Calculate cosine similarities between query and all chunks
            similarities = cosine_similarity(query_embedding, chunk_embeddings)[0]
            
            # Create scored chunks
            scored_chunks = []
            for i, (chunk, similarity) in enumerate(zip(chunks, similarities)):
                scored_chunks.append(RelevantChunk(
                    chunk=chunk,
                    score=float(similarity),
                    similarity=float(similarity)
                ))
            
            # Sort by similarity and return top k
            scored_chunks.sort(key=lambda x: x.similarity, reverse=True)
            result = scored_chunks[:top_k]
            
            logger.info(f"🔍 Found {len(result)} similar chunks using on-the-fly search")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in on-the-fly search: {e}")
            return []
    
    async def remove_session(self, session_id: str) -> None:
        """Remove ChromaDB collection for a session"""
        try:
            if session_id in self.session_collections:
                collection_name = self.session_collections[session_id]
                
                # Delete the collection from ChromaDB
                try:
                    self.chroma_client.delete_collection(name=collection_name)
                    logger.info(f"🗑️ Deleted ChromaDB collection '{collection_name}' for session {session_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not delete collection '{collection_name}': {e}")
                
                # Remove from tracking
                del self.session_collections[session_id]
            else:
                logger.info(f"ℹ️ No ChromaDB collection found for session {session_id}")
                
        except Exception as e:
            logger.error(f"❌ Error removing session {session_id}: {e}")
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session"""
        stats = {
            "has_collection": False,
            "chunk_count": 0,
            "collection_name": None
        }
        
        try:
            if session_id in self.session_collections:
                collection_name = self.session_collections[session_id]
                collection = self.chroma_client.get_collection(name=collection_name)
                
                stats["has_collection"] = True
                stats["chunk_count"] = collection.count()
                stats["collection_name"] = collection_name
        except Exception as e:
            logger.error(f"❌ Error getting session stats: {e}")
        
        return stats

# Global vector service instance
vector_service = VectorService() 