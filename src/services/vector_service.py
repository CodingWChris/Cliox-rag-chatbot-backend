import re
import logging
from typing import List, Dict, Any
from ..models.knowledge import KnowledgeChunk

logger = logging.getLogger(__name__)

class RelevantChunk:
    def __init__(self, chunk: KnowledgeChunk, score: float = 0.0):
        self.id = chunk.id
        self.content = chunk.content
        self.metadata = chunk.metadata
        self.score = score

class VectorService:
    def search_similar(
        self, 
        query: str, 
        chunks: List[KnowledgeChunk], 
        top_k: int = 3
    ) -> List[RelevantChunk]:
        """
        Simple keyword-based similarity search
        TODO: Replace with proper embeddings + cosine similarity later
        """
        
        # Preprocess query
        query_terms = [
            term.lower().strip() 
            for term in re.split(r'\W+', query) 
            if len(term) > 2
        ]
        
        if not query_terms:
            return []
        
        scored_chunks = []
        
        for chunk in chunks:
            score = self._calculate_score(query_terms, chunk)
            if score > 0:
                scored_chunks.append(RelevantChunk(chunk, score))
        
        # Sort by score (descending) and return top k
        scored_chunks.sort(key=lambda x: x.score, reverse=True)
        return scored_chunks[:top_k]
    
    def _calculate_score(self, query_terms: List[str], chunk: KnowledgeChunk) -> float:
        """Calculate relevance score for a chunk"""
        content = chunk.content.lower()
        metadata_text = " ".join(str(v) for v in chunk.metadata.values()).lower()
        
        score = 0.0
        
        for term in query_terms:
            # Count matches in content (weighted more heavily)
            content_matches = len(re.findall(re.escape(term), content))
            score += content_matches * 2.0
            
            # Count matches in metadata
            metadata_matches = len(re.findall(re.escape(term), metadata_text))
            score += metadata_matches * 1.0
        
        # Normalize by content length to avoid bias toward longer chunks
        content_length = max(len(content.split()), 1)
        normalized_score = score / (content_length ** 0.5)
        
        return normalized_score

# Global vector service instance
vector_service = VectorService() 