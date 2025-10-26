"""
Advanced RAG (Retrieval-Augmented Generation) for Educational Content
"""

import os
import re
import logging
import asyncio
import math
import string
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


class EducationalRAG:
    """
    Advanced RAG system for educational content retrieval
    Uses ChromaDB for vector storage and BM25 for keyword search
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
        
        # BM25 components
        self.bm25_index = None
        self.bm25_corpus = []  # Store tokenized documents
        self.bm25_documents = []  # Store original documents
        self.bm25_metadatas = []  # Store document metadata
        self.bm25_ids = []  # Store document IDs
        
        # Preprocessing settings
        self.stopwords = set([
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'the', 'this', 'these', 'those',
            'i', 'you', 'we', 'they', 'what', 'which', 'who', 'when', 'where',
            'why', 'how', 'can', 'could', 'would', 'should', 'may', 'might'
        ])
        
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
                
                # Initialize BM25 if rank-bm25 is available
                try:
                    from rank_bm25 import BM25Okapi
                    self.BM25Okapi = BM25Okapi
                    self.initialized = True
                    print("BM25 library loaded successfully - hybrid search available")
                    logger.info("BM25 initialized successfully - hybrid search available")
                except ImportError as e:
                    print(f"BM25 library not loaded: {e}")
                    logger.warning("rank-bm25 not installed - hybrid search limited")
                    logger.info("Install with: pip install rank-bm25")
                    self.initialized = True  # Still allow semantic search
                    
            except ImportError:
                logger.warning("sentence-transformers not installed - semantic search limited")
                self.initialized = False
                
        except ImportError:
            logger.warning("ChromaDB not installed - advanced RAG features unavailable")
            logger.info("Install with: pip install chromadb sentence-transformers rank-bm25")
            self.initialized = False
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            self.initialized = False
        
        if self.initialized:
            logger.info("Educational RAG system initialized successfully")
        else:
            logger.warning("Educational RAG system running in fallback mode")
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize and preprocess text for BM25
        
        Args:
            text: Raw text to tokenize
            
        Returns:
            List of processed tokens
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Split into tokens
        tokens = text.split()
        
        # Remove stopwords and short tokens
        tokens = [
            token for token in tokens 
            if token not in self.stopwords and len(token) > 2
        ]
        
        return tokens
    
    def _build_bm25_index(self):
        """Build or rebuild the BM25 index from current corpus"""
        if hasattr(self, 'BM25Okapi') and self.bm25_corpus:
            self.bm25_index = self.BM25Okapi(self.bm25_corpus)
            logger.info(f"Built BM25 index with {len(self.bm25_corpus)} documents")
    
    async def index_educational_content(
        self,
        content_list: List[Dict[str, Any]]
    ) -> bool:
        """
        Index educational content for both semantic and keyword retrieval
        
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
            
            # Prepare documents for ChromaDB
            documents = []
            metadatas = []
            ids = []
            
            for idx, content in enumerate(content_list):
                doc_text = content.get('text', '')
                doc_metadata = content.get('metadata', {})
                doc_id = content.get('id', f"doc_{idx}")
                
                documents.append(doc_text)
                metadatas.append(doc_metadata)
                ids.append(doc_id)
                
                # Also prepare for BM25 indexing
                if hasattr(self, 'BM25Okapi'):
                    tokenized_doc = self._tokenize(doc_text)
                    self.bm25_corpus.append(tokenized_doc)
                    self.bm25_documents.append(doc_text)
                    self.bm25_metadatas.append(doc_metadata)
                    self.bm25_ids.append(doc_id)
            
            # Add to ChromaDB collection - wrap blocking call in thread pool
            await asyncio.to_thread(
                self.collection.add,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            # Build BM25 index if available
            if hasattr(self, 'BM25Okapi'):
                self._build_bm25_index()
                logger.info(f"Indexed {len(content_list)} documents in both ChromaDB and BM25")
            else:
                logger.info(f"Indexed {len(content_list)} documents in ChromaDB only")
            
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
        Retrieve relevant educational content using semantic search
        
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
                    # Convert L2 distance to similarity score
                    score = 1.0 / (1.0 + distance)
                    
                    # Determine relevance based on score
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
                        'relevance': relevance,
                        'source': 'semantic'
                    })
            
            logger.info(f"Retrieved {len(retrieved_content)} relevant documents via semantic search")
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
        Perform keyword-based search using BM25
        
        Args:
            query: Search query
            top_k: Number of results
            
        Returns:
            List of keyword-matched content
        """
        if not hasattr(self, 'BM25Okapi') or not self.bm25_index:
            logger.info("BM25 not available - using semantic search as fallback")
            return await self.semantic_search(query, top_k)
        
        try:
            logger.info(f"Performing BM25 keyword search for: {query}")
            
            # Tokenize query using same preprocessing as documents
            tokenized_query = self._tokenize(query)
            
            # Get BM25 scores
            scores = self.bm25_index.get_scores(tokenized_query)
            
            # Get top-k indices
            top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
            
            # Build results
            keyword_results = []
            for idx in top_indices:
                if scores[idx] > 0:  # Only include documents with positive scores
                    # Normalize BM25 score (typically ranges from 0 to ~10-20)
                    # Using sigmoid-like normalization for better 0-1 mapping
                    normalized_score = 1 - math.exp(-scores[idx] / 10)
                    
                    keyword_results.append({
                        'content': self.bm25_documents[idx],
                        'metadata': self.bm25_metadatas[idx] if idx < len(self.bm25_metadatas) else {},
                        'score': normalized_score,
                        'bm25_raw_score': float(scores[idx]),
                        'relevance': 'high' if normalized_score > 0.5 else 'medium' if normalized_score > 0.2 else 'low',
                        'source': 'bm25'
                    })
            
            logger.info(f"Retrieved {len(keyword_results)} documents via BM25 search")
            return keyword_results
            
        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            logger.info("Falling back to semantic search")
            return await self.semantic_search(query, top_k)
    
    async def hybrid_search(
        self,
        query: str,
        subject: Optional[str] = None,
        student_level: Optional[str] = None,
        top_k: int = 10,
        semantic_weight: float = 0.5,
        bm25_weight: float = 0.5,
        fusion_method: str = "weighted"  # "weighted" or "rrf"
    ) -> List[Dict[str, Any]]:
        """
        True hybrid search combining semantic and BM25 keyword search
        
        Args:
            query: Search query
            subject: Filter by subject
            student_level: Filter by level
            top_k: Number of results
            semantic_weight: Weight for semantic results (0-1)
            bm25_weight: Weight for BM25 results (0-1)
            fusion_method: Method to combine results ("weighted" or "rrf")
            
        Returns:
            List of combined search results
        """
        try:
            logger.info(f"Performing hybrid search with method: {fusion_method}")
            
            # Normalize weights
            total_weight = semantic_weight + bm25_weight
            if total_weight > 0:
                semantic_weight = semantic_weight / total_weight
                bm25_weight = bm25_weight / total_weight
            else:
                semantic_weight = 0.5
                bm25_weight = 0.5
            
            # Run both searches in parallel
            semantic_task = asyncio.create_task(
                self.retrieve_educational_content(
                    query, subject, student_level, top_k * 2
                )
            )
            keyword_task = asyncio.create_task(
                self.keyword_search(query, top_k * 2)
            )
            
            # Wait for both to complete
            semantic_results, keyword_results = await asyncio.gather(
                semantic_task, keyword_task
            )
            
            # Combine results based on method
            if fusion_method == "rrf":
                combined = self._reciprocal_rank_fusion(
                    semantic_results, 
                    keyword_results,
                    k=60  # RRF parameter
                )
            else:  # weighted
                combined = self._weighted_fusion(
                    semantic_results,
                    keyword_results,
                    semantic_weight,
                    bm25_weight
                )
            
            # Filter by subject and level if specified
            if subject or student_level:
                combined = self._filter_by_criteria(combined, subject, student_level)
            
            # Return top_k results
            final_results = combined[:top_k]
            
            # Log statistics
            logger.info(
                f"Hybrid search complete - "
                f"Semantic: {len(semantic_results)}, "
                f"BM25: {len(keyword_results)}, "
                f"Combined: {len(combined)}, "
                f"Final: {len(final_results)}"
            )
            
            return final_results
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            # Fallback to semantic search
            return await self.retrieve_educational_content(
                query, subject, student_level, top_k
            )
    
    def _weighted_fusion(
        self,
        semantic_results: List[Dict],
        keyword_results: List[Dict],
        semantic_weight: float,
        keyword_weight: float
    ) -> List[Dict]:
        """
        Combine results using weighted score fusion
        
        Args:
            semantic_results: Results from semantic search
            keyword_results: Results from BM25 search
            semantic_weight: Weight for semantic scores
            keyword_weight: Weight for BM25 scores
            
        Returns:
            Combined and sorted results
        """
        combined_dict = {}
        
        # Add semantic results
        for result in semantic_results:
            content = result['content']
            score = result.get('score', 0) * semantic_weight
            combined_dict[content] = {
                **result,
                'combined_score': score,
                'semantic_score': result.get('score', 0),
                'sources': ['semantic']
            }
        
        # Add/update with keyword results
        for result in keyword_results:
            content = result['content']
            score = result.get('score', 0) * keyword_weight
            
            if content in combined_dict:
                # Document found in both - combine scores
                combined_dict[content]['combined_score'] += score
                combined_dict[content]['bm25_score'] = result.get('score', 0)
                combined_dict[content]['sources'].append('bm25')
            else:
                # Document only in BM25
                combined_dict[content] = {
                    **result,
                    'combined_score': score,
                    'bm25_score': result.get('score', 0),
                    'sources': ['bm25']
                }
        
        # Sort by combined score
        combined = sorted(
            combined_dict.values(),
            key=lambda x: x['combined_score'],
            reverse=True
        )
        
        # Update relevance based on combined score
        for doc in combined:
            score = doc['combined_score']
            if score > 0.6:
                doc['relevance'] = 'high'
            elif score > 0.3:
                doc['relevance'] = 'medium'
            else:
                doc['relevance'] = 'low'
        
        return combined
    
    def _reciprocal_rank_fusion(
        self,
        semantic_results: List[Dict],
        keyword_results: List[Dict],
        k: int = 60
    ) -> List[Dict]:
        """
        Combine results using Reciprocal Rank Fusion (RRF)
        
        RRF score = sum(1 / (k + rank_in_list))
        
        Args:
            semantic_results: Results from semantic search
            keyword_results: Results from BM25 search
            k: RRF parameter (typically 60)
            
        Returns:
            Combined and sorted results
        """
        rrf_scores = defaultdict(float)
        doc_data = {}
        
        # Process semantic results
        for rank, result in enumerate(semantic_results, 1):
            content = result['content']
            rrf_scores[content] += 1 / (k + rank)
            if content not in doc_data:
                doc_data[content] = {
                    **result,
                    'semantic_rank': rank,
                    'sources': ['semantic']
                }
            else:
                doc_data[content]['semantic_rank'] = rank
                doc_data[content]['sources'].append('semantic')
        
        # Process keyword results
        for rank, result in enumerate(keyword_results, 1):
            content = result['content']
            rrf_scores[content] += 1 / (k + rank)
            if content not in doc_data:
                doc_data[content] = {
                    **result,
                    'bm25_rank': rank,
                    'sources': ['bm25']
                }
            else:
                doc_data[content]['bm25_rank'] = rank
                if 'bm25' not in doc_data[content]['sources']:
                    doc_data[content]['sources'].append('bm25')
        
        # Build final results
        combined = []
        for content, rrf_score in rrf_scores.items():
            doc = doc_data[content].copy()
            doc['rrf_score'] = rrf_score
            # Normalize RRF score to 0-1 range for consistency
            doc['combined_score'] = min(rrf_score * k / 2, 1.0)  
            
            # Update relevance
            if doc['combined_score'] > 0.6:
                doc['relevance'] = 'high'
            elif doc['combined_score'] > 0.3:
                doc['relevance'] = 'medium'
            else:
                doc['relevance'] = 'low'
            
            combined.append(doc)
        
        # Sort by RRF score
        combined.sort(key=lambda x: x['rrf_score'], reverse=True)
        
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
    
    async def get_search_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the current index
        
        Returns:
            Dictionary with index statistics
        """
        stats = {
            'chromadb_initialized': self.collection is not None,
            'bm25_initialized': self.bm25_index is not None,
            'bm25_available': hasattr(self, 'BM25Okapi'),  # Whether BM25 library is available
            'hybrid_search_available': hasattr(self, 'BM25Okapi'),  # Based on library availability, not index
            'total_documents': len(self.bm25_documents) if self.bm25_documents else 0,
            'embedder_available': self.embedder is not None,
            'collection_name': self.collection_name,
            'persist_directory': self.persist_directory
        }
        
        if self.collection:
            try:
                # Get ChromaDB collection stats
                import asyncio
                count = await asyncio.to_thread(self.collection.count)
                stats['chromadb_document_count'] = count
            except:
                stats['chromadb_document_count'] = 'unknown'
        
        return stats


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
        print("Testing Educational RAG System with Hybrid Search...")
        print("=" * 60)
        
        # Create RAG system
        rag, reranker = create_rag_system()
        
        if not rag.initialized:
            print("RAG system not initialized - install dependencies")
            print("Run: pip install chromadb sentence-transformers rank-bm25")
            return
        
        # Check search capabilities
        stats = await rag.get_search_statistics()
        print("\nSystem Capabilities:")
        print(f"  - ChromaDB: {'Working' if stats['chromadb_initialized'] else 'Not working'}")
        print(f"  - BM25: {'Working' if stats['bm25_initialized'] else 'Not working'}")
        print(f"  - Hybrid Search: {'Working' if stats['hybrid_search_available'] else 'Not working'}")
        print(f"  - Embedder: {'Working' if stats['embedder_available'] else 'Not working'}")
        
        # Sample educational content
        sample_content = [
            {
                'id': 'py_lists_1',
                'text': 'Python lists are ordered, mutable collections that can store items of different types. You can add items using append() and remove them using pop().',
                'metadata': {
                    'subject': 'programming',
                    'level': 'beginner',
                    'topic': 'python lists'
                }
            },
            {
                'id': 'py_loops_1',
                'text': 'For loops in Python allow you to iterate over sequences like lists, tuples, and strings. The range() function is commonly used with for loops.',
                'metadata': {
                    'subject': 'programming',
                    'level': 'beginner',
                    'topic': 'python loops'
                }
            },
            {
                'id': 'py_functions_1',
                'text': 'Functions in Python are defined using the def keyword. They help organize code and make it reusable. Functions can accept parameters and return values.',
                'metadata': {
                    'subject': 'programming',
                    'level': 'intermediate',
                    'topic': 'python functions'
                }
            },
            {
                'id': 'math_calc_1',
                'text': 'Derivatives measure the rate of change of a function. The derivative of x² is 2x. This concept is fundamental in calculus.',
                'metadata': {
                    'subject': 'mathematics',
                    'level': 'advanced',
                    'topic': 'calculus'
                }
            },
            {
                'id': 'math_algebra_1',
                'text': 'Linear equations have the form ax + b = c. To solve, isolate x by performing inverse operations. Always do the same operation to both sides.',
                'metadata': {
                    'subject': 'mathematics',
                    'level': 'beginner',
                    'topic': 'algebra'
                }
            }
        ]
        
        # Index content
        print("\nIndexing sample content...")
        success = await rag.index_educational_content(sample_content)
        print(f"  Indexed {len(sample_content)} documents: {'Working' if success else 'Not working'}")
        
        # Test different search methods
        test_query = "How do Python functions work with parameters?"
        print(f"\nTesting search methods for: '{test_query}'")
        print("-" * 60)
        
        # 1. Semantic Search
        print("\n1 Semantic Search Results:")
        semantic_results = await rag.semantic_search(test_query, top_k=3)
        for i, result in enumerate(semantic_results, 1):
            print(f"  {i}. Score: {result['score']:.3f} | {result['content'][:80]}...")
        
        # 2. BM25 Keyword Search
        print("\n2 BM25 Keyword Search Results:")
        keyword_results = await rag.keyword_search(test_query, top_k=3)
        for i, result in enumerate(keyword_results, 1):
            score_info = f"Score: {result['score']:.3f}"
            if 'bm25_raw_score' in result:
                score_info += f" (Raw: {result['bm25_raw_score']:.2f})"
            print(f"  {i}. {score_info} | {result['content'][:80]}...")
        
        # 3. Hybrid Search (Weighted)
        print("\n3 Hybrid Search Results (Weighted Fusion):")
        hybrid_results_weighted = await rag.hybrid_search(
            test_query,
            top_k=3,
            semantic_weight=0.6,
            bm25_weight=0.4,
            fusion_method="weighted"
        )
        for i, result in enumerate(hybrid_results_weighted, 1):
            sources = ', '.join(result.get('sources', ['unknown']))
            print(f"  {i}. Score: {result['combined_score']:.3f} | Sources: [{sources}]")
            print(f"     {result['content'][:80]}...")
        
        # 4. Hybrid Search (RRF)
        print("\n4️⃣ Hybrid Search Results (RRF Fusion):")
        hybrid_results_rrf = await rag.hybrid_search(
            test_query,
            top_k=3,
            fusion_method="rrf"
        )
        for i, result in enumerate(hybrid_results_rrf, 1):
            sources = ', '.join(result.get('sources', ['unknown']))
            rrf_info = f"RRF: {result.get('rrf_score', 0):.4f}" if 'rrf_score' in result else ""
            print(f"  {i}. Score: {result['combined_score']:.3f} {rrf_info} | Sources: [{sources}]")
            print(f"     {result['content'][:80]}...")
        
        # Test with filters
        print("\n5 Filtered Hybrid Search (Programming/Beginner):")
        filtered_results = await rag.hybrid_search(
            "How to use lists in Python?",
            subject="programming",
            student_level="beginner",
            top_k=2
        )
        for i, result in enumerate(filtered_results, 1):
            metadata = result.get('metadata', {})
            print(f"  {i}. {metadata.get('subject')}/{metadata.get('level')} | Score: {result['combined_score']:.3f}")
            print(f"     {result['content'][:80]}...")
        
        # Test reranking if available
        if reranker.initialized and hybrid_results_weighted:
            print("\n6 Re-ranked Results:")
            reranked = reranker.rerank_for_learning(
                hybrid_results_weighted,
                test_query,
                top_k=2
            )
            for i, result in enumerate(reranked, 1):
                print(f"  {i}. Rerank Score: {result['rerank_score']:.3f} | {result['content'][:80]}...")
        
        print("\n" + "=" * 60)
        print(" RAG system test complete!")
        print("\nKey Features Demonstrated:")
        print("  • Semantic search using embeddings")
        print("  • BM25 keyword search")
        print("  • Hybrid search with weighted fusion")
        print("  • Hybrid search with RRF fusion")
        print("  • Subject and level filtering")
        if reranker.initialized:
            print("  • Cross-encoder re-ranking")
    
    # Run test
    asyncio.run(test_rag())
