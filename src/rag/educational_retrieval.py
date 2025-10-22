"""
Advanced RAG (Retrieval-Augmented Generation) for Educational Content
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class EducationalRAG:
    """
    Advanced RAG system for educational content retrieval
    Uses ChromaDB for vector storage and semantic search
    """
    
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        collection_name: str = "educational_content"
    ):
        """
        Initialize Educational RAG system
        
        Args:
            persist_directory: Directory to persist vector database
            collection_name: Name of the collection
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.chroma_client = None
        self.collection = None
        self.embedder = None
        self.initialized = False
        
        # Try to initialize ChromaDB
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Create persistent client
            self.chroma_client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            try:
                self.collection = self.chroma_client.get_collection(name=collection_name)
                logger.info(f"Loaded existing collection: {collection_name}")
            except:
                self.collection = self.chroma_client.create_collection(
                    name=collection_name,
                    metadata={"description": "Educational content for multi-agent tutor"}
                )
                logger.info(f"Created new collection: {collection_name}")
            
            # Initialize embedder
            try:
                from sentence_transformers import SentenceTransformer
                
                # Import device detection
                try:
                    from utils.device_config import get_optimal_device
                    device = get_optimal_device()
                except ImportError:
                    logger.warning("device_config not available, using cpu")
                    device = 'cpu'
                
                self.embedder = SentenceTransformer('all-MiniLM-L6-v2', device=device)
                logger.info(f"Initialized sentence transformer embedder on {device.upper()}")
                self.initialized = True
            except ImportError:
                logger.warning("sentence-transformers not installed - semantic search limited")
                self.initialized = False
                
        except ImportError:
            logger.warning("ChromaDB not installed - advanced RAG features unavailable")
            logger.info("Install with: pip install chromadb sentence-transformers")
            self.initialized = False
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            self.initialized = False
        
        if self.initialized:
            logger.info("Educational RAG system initialized successfully")
        else:
            logger.warning("Educational RAG system running in fallback mode")
    
    async def index_educational_content(
        self,
        content_list: List[Dict[str, Any]]
    ) -> bool:
        """
        Index educational content for retrieval
        
        Args:
            content_list: List of content dictionaries with 'text', 'metadata'
            
        Returns:
            True if successful, False otherwise
        """
        if not self.initialized:
            logger.warning("RAG not initialized - cannot index content")
            return False
        
        try:
            import asyncio
            logger.info(f"Indexing {len(content_list)} educational resources")
            
            # Prepare documents
            documents = []
            metadatas = []
            ids = []
            
            for idx, content in enumerate(content_list):
                documents.append(content.get('text', ''))
                metadatas.append(content.get('metadata', {}))
                ids.append(content.get('id', f"doc_{idx}"))
            
            # Add to collection - wrap blocking call in thread pool
            await asyncio.to_thread(
                self.collection.add,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Successfully indexed {len(content_list)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Failed to index content: {e}")
            return False
    
    async def retrieve_educational_content(
        self,
        query: str,
        subject: Optional[str] = None,
        student_level: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant educational content
        
        Args:
            query: Search query
            subject: Filter by subject (optional)
            student_level: Filter by difficulty level (optional)
            top_k: Number of results to return
            
        Returns:
            List of relevant content dictionaries
        """
        if not self.initialized:
            logger.warning("RAG not initialized - returning empty results")
            return []
        
        try:
            import asyncio
            logger.info(f"Retrieving educational content for: {query}")
            
            # Build where clause for filtering (ChromaDB format)
            where_clause = None
            if subject and student_level:
                where_clause = {
                    "$and": [
                        {"subject": {"$eq": subject}},
                        {"level": {"$eq": student_level}}
                    ]
                }
            elif subject:
                where_clause = {"subject": {"$eq": subject}}
            elif student_level:
                where_clause = {"level": {"$eq": student_level}}
            
            # Query the collection - wrap blocking call in thread pool
            results = await asyncio.to_thread(
                self.collection.query,
                query_texts=[query],
                n_results=top_k,
                where=where_clause
            )
            
            # Format results
            retrieved_content = []
            if results and results['documents'] and len(results['documents']) > 0:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0] if results['metadatas'] else [{}] * len(documents)
                distances = results['distances'][0] if results['distances'] else [0] * len(documents)
                
                for doc, metadata, distance in zip(documents, metadatas, distances):
                    # Convert L2 distance to similarity score using bounded monotonic mapping
                    # This handles L2 distances (which can be > 1.0) appropriately
                    score = 1.0 / (1.0 + distance)
                    
                    # Determine relevance based on L2-appropriate thresholds
                    # Higher scores (closer to 1.0) indicate better matches
                    if score > 0.66:
                        relevance = 'high'
                    elif score > 0.33:
                        relevance = 'medium'
                    else:
                        relevance = 'low'
                    
                    retrieved_content.append({
                        'content': doc,
                        'metadata': metadata,
                        'score': score,
                        'relevance': relevance
                    })
            
            logger.info(f"Retrieved {len(retrieved_content)} relevant documents")
            return retrieved_content
            
        except Exception as e:
            logger.error(f"Failed to retrieve content: {e}")
            return []
    
    async def semantic_search(
        self,
        query: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using embeddings
        
        Args:
            query: Search query
            top_k: Number of results
            
        Returns:
            List of semantically similar content
        """
        return await self.retrieve_educational_content(query, top_k=top_k)
    
    async def keyword_search(
        self,
        query: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform keyword-based search (BM25)
        
        Args:
            query: Search query
            top_k: Number of results
            
        Returns:
            List of keyword-matched content
        """
        # This would use BM25 in production
        # For now, fallback to semantic search
        logger.info("Using semantic search as keyword search fallback")
        return await self.semantic_search(query, top_k)
    
    async def hybrid_search(
        self,
        query: str,
        subject: Optional[str] = None,
        student_level: Optional[str] = None,
        top_k: int = 10,
        semantic_weight: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Combine semantic and keyword search
        
        Args:
            query: Search query
            subject: Filter by subject
            student_level: Filter by level
            top_k: Number of results
            semantic_weight: Weight for semantic results (0-1)
            
        Returns:
            List of combined search results
        """
        logger.info(f"Performing hybrid search for: {query}")
        
        try:
            # Get semantic results
            semantic_results = await self.semantic_search(query, top_k=top_k * 2)
            
            # Get keyword results (currently fallback to semantic)
            keyword_results = await self.keyword_search(query, top_k=top_k * 2)
            
            # Combine results with weighted scoring
            combined = self._combine_search_results(
                semantic_results,
                keyword_results,
                semantic_weight=semantic_weight,
                keyword_weight=1.0 - semantic_weight
            )
            
            # Filter by subject and level if specified
            if subject or student_level:
                combined = self._filter_by_criteria(combined, subject, student_level)
            
            # Return top_k results
            return combined[:top_k]
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []
    
    def _combine_search_results(
        self,
        semantic_results: List[Dict],
        keyword_results: List[Dict],
        semantic_weight: float,
        keyword_weight: float
    ) -> List[Dict]:
        """Combine and re-score results from different search methods"""
        # Simple combination - in production would be more sophisticated
        combined_dict = {}
        
        # Add semantic results
        for result in semantic_results:
            content = result['content']
            score = result.get('score', 0) * semantic_weight
            combined_dict[content] = {
                **result,
                'combined_score': score
            }
        
        # Add/update with keyword results
        for result in keyword_results:
            content = result['content']
            score = result.get('score', 0) * keyword_weight
            if content in combined_dict:
                combined_dict[content]['combined_score'] += score
            else:
                combined_dict[content] = {
                    **result,
                    'combined_score': score
                }
        
        # Sort by combined score
        combined = sorted(
            combined_dict.values(),
            key=lambda x: x['combined_score'],
            reverse=True
        )
        
        return combined
    
    def _filter_by_criteria(
        self,
        results: List[Dict],
        subject: Optional[str],
        level: Optional[str]
    ) -> List[Dict]:
        """Filter results by subject and level"""
        filtered = []
        for result in results:
            metadata = result.get('metadata', {})
            
            if subject and metadata.get('subject') != subject:
                continue
            if level and metadata.get('level') != level:
                continue
            
            filtered.append(result)
        
        return filtered


class EducationalReranker:
    """
    Re-ranks search results for educational relevance
    Uses cross-encoder for more accurate relevance scoring
    """
    
    def __init__(self):
        """Initialize the reranker"""
        self.cross_encoder = None
        self.initialized = False
        
        try:
            from sentence_transformers import CrossEncoder
            try:
                from utils.device_config import get_optimal_device
                device = get_optimal_device()
            except ImportError:
                logger.warning("device_config not available, using cpu")
                device = 'cpu'
            
            self.cross_encoder = CrossEncoder(
                'cross-encoder/ms-marco-MiniLM-L-6-v2',
                device=device
            )
            self.initialized = True
            logger.info(f"Educational reranker initialized on {device.upper()}")
        except ImportError:
            logger.warning("sentence-transformers not available - reranking limited")
        except Exception as e:
            logger.error(f"Failed to initialize reranker: {e}")
    
    def _normalize_scores(self, scores) -> list:
        """
        Normalize cross-encoder scores to 0-1 range using sigmoid 
        Makes negative scores interpretable as low relevance
        
        Args:
            scores: Raw cross-encoder scores (logits)
            
        Returns:
            List of normalized scores between 0 and 1
        """
        import math
        
        # Convert to list if numpy array
        if hasattr(scores, 'tolist'):
            scores = scores.tolist()
        
        # Apply sigmoid normalization: 1 / (1 + e^(-x))
        normalized = [1 / (1 + math.exp(-score)) for score in scores]
        return normalized
    
    def rerank_for_learning(
        self,
        candidates: List[Dict[str, Any]],
        query: str,
        student_level: Optional[str] = None,
        top_k: Optional[int] = None,
        normalize: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Re-rank results for educational relevance
        
        Args:
            candidates: List of candidate results
            query: Original query
            student_level: Student's level for filtering
            top_k: Number of results to return
            normalize: Whether to normalize scores to 0-1 range (recommended)
            
        Returns:
            Re-ranked list of results
        """
        if not self.initialized or not candidates:
            return candidates
        
        try:
            logger.info(f"Re-ranking {len(candidates)} candidates")
            
            # Prepare query-document pairs
            pairs = [
                (query, candidate.get('content', ''))
                for candidate in candidates
            ]
            
            # Score with cross-encoder (returns raw logits)
            scores = self.cross_encoder.predict(pairs)
            
            # Log raw score range for debugging
            logger.debug(f"Raw score range: [{min(scores):.3f}, {max(scores):.3f}]")
            
            # Normalize scores if requested 
            if normalize:
                normalized_scores = self._normalize_scores(scores)
                logger.debug(f"Normalized score range: [{min(normalized_scores):.3f}, {max(normalized_scores):.3f}]")
            else:
                normalized_scores = scores
            
            # Update candidates with new scores
            for candidate, raw_score, norm_score in zip(candidates, scores, normalized_scores):
                candidate['rerank_score'] = float(norm_score)
                candidate['rerank_score_raw'] = float(raw_score)  # Keep raw for debugging
            
            # Filter by level if specified
            if student_level:
                candidates = self._filter_by_level(candidates, student_level)
            
            # Sort by rerank score
            reranked = sorted(
                candidates,
                key=lambda x: x.get('rerank_score', 0),
                reverse=True
            )
            
            # Return top_k if specified
            if top_k:
                reranked = reranked[:top_k]
            
            logger.info(f"Re-ranking complete - returned {len(reranked)} results")
            return reranked
            
        except Exception as e:
            logger.error(f"Re-ranking failed: {e}")
            return candidates
    
    def _filter_by_level(
        self,
        candidates: List[Dict],
        student_level: str
    ) -> List[Dict]:
        """Filter results appropriate for student level"""
        level_hierarchy = ['beginner', 'intermediate', 'advanced']
        try:
            student_level_idx = level_hierarchy.index(student_level)
        except ValueError:
            return candidates
        
        filtered = []
        for candidate in candidates:
            metadata = candidate.get('metadata', {})
            content_level = metadata.get('level', 'beginner')
            
            try:
                content_level_idx = level_hierarchy.index(content_level)
                # Include content at or below student level
                if content_level_idx <= student_level_idx:
                    filtered.append(candidate)
            except ValueError:
                # If level not in hierarchy, include by default
                filtered.append(candidate)
        
        return filtered


def create_rag_system(
    persist_directory: str = "./chroma_db",
    collection_name: str = "educational_content"
) -> tuple:
    """
    Factory function to create RAG system and reranker
    
    Args:
        persist_directory: Directory for vector database
        collection_name: Name of the collection
        
    Returns:
        Tuple of (EducationalRAG, EducationalReranker)
    """
    rag = EducationalRAG(
        persist_directory=persist_directory,
        collection_name=collection_name
    )
    reranker = EducationalReranker()
    
    return rag, reranker


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_rag():
        """Test the RAG system"""
        print("Testing Educational RAG System...")
        
        # Create RAG system
        rag, reranker = create_rag_system()
        
        if not rag.initialized:
            print("RAG system not initialized - install dependencies")
            return
        
        # Sample educational content
        sample_content = [
            {
                'id': 'py_lists_1',
                'text': 'Python lists are ordered, mutable collections that can store items of different types.',
                'metadata': {
                    'subject': 'programming',
                    'level': 'beginner',
                    'topic': 'python lists'
                }
            },
            {
                'id': 'py_loops_1',
                'text': 'For loops in Python allow you to iterate over sequences like lists, tuples, and strings.',
                'metadata': {
                    'subject': 'programming',
                    'level': 'beginner',
                    'topic': 'python loops'
                }
            }
        ]
        
        # Index content
        success = await rag.index_educational_content(sample_content)
        print(f"Indexed content: {success}")
        
        # Retrieve content
        results = await rag.retrieve_educational_content(
            query="How do Python lists work?",
            subject="programming",
            student_level="beginner",
            top_k=2
        )
        
        print(f"Retrieved {len(results)} results")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['content'][:80]}... (score: {result['score']:.3f})")
        
        print("\nRAG system test complete!")
    
    # Run test
    asyncio.run(test_rag())
