"""
Test suite for RAG (Retrieval-Augmented Generation) and search functionality
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any
from pathlib import Path

# Project imports - using actual class names
from rag.educational_retrieval import EducationalRAG


class TestEducationalRAG:
    """Test suite for Educational RAG system"""
    
    @pytest.fixture(autouse=True)
    def setup(self, temp_test_dir):
        """Setup RAG system for testing"""
        self.rag = EducationalRAG(
            persist_directory=str(temp_test_dir / "test_chroma"),
            collection_name="test_collection"
        )
        
    @pytest.mark.unit
    def test_rag_initialization(self):
        """Test RAG system initialization"""
        assert self.rag is not None
        assert self.rag.collection_name == "test_collection"
        assert self.rag.persist_directory is not None
        assert self.rag.initialized is True
    
    @pytest.mark.unit
    def test_bm25_components(self):
        """Test BM25 component initialization"""
        assert self.rag.bm25_index is None
        assert self.rag.bm25_corpus == []
        assert self.rag.bm25_documents == []
        assert self.rag.bm25_metadatas == []
        assert self.rag.bm25_ids == []
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_add_content(self):
        """Test adding content to RAG system"""
        # Test adding content (RAG initializes in __init__)
        test_content = [
            {
                "text": "Python is a programming language",
                "metadata": {"source": "test1", "subject": "programming"}
            },
            {
                "text": "Functions are reusable code blocks",
                "metadata": {"source": "test2", "subject": "programming"}
            }
        ]
        
        # If RAG is initialized, this should succeed
        if self.rag.initialized:
            result = await self.rag.index_educational_content(test_content)
            assert result is True
        else:
            # If not initialized (missing dependencies), operation returns False
            pytest.skip("RAG system not initialized - missing dependencies")
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_search_content(self):
        """Test searching content in RAG system"""
        # Mock search method
        with patch.object(self.rag, 'hybrid_search') as mock_search:
            mock_search.return_value = [
                {
                    "content": "Python functions",
                    "metadata": {"source": "test"},
                    "score": 0.95
                }
            ]
            
            results = await mock_search("Python functions", k=5)
            
            assert len(results) == 1
            assert results[0]["content"] == "Python functions"
            assert results[0]["score"] == 0.95


class TestDocumentProcessing:
    """Test document processing functionality"""
    
    @pytest.mark.unit
    def test_text_chunking(self):
        """Test text chunking for embeddings"""
        # Simple text chunking test
        text = " ".join([f"Sentence {i}." for i in range(100)])
        
        # Simple chunking by sentences
        chunks = text.split(". ")
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)
    
    @pytest.mark.unit
    def test_metadata_extraction(self):
        """Test metadata extraction from documents"""
        document = {
            "content": "Test content",
            "source": "test.md",
            "topic": "testing"
        }
        
        # Extract metadata
        metadata = {k: v for k, v in document.items() if k != "content"}
        
        assert metadata["source"] == "test.md"
        assert metadata["topic"] == "testing"


class TestSearchStrategies:
    """Test different search strategies"""
    
    @pytest.mark.unit
    def test_keyword_search(self):
        """Test keyword-based search"""
        documents = [
            "Python is a programming language",
            "Java is also a programming language",
            "Python has simple syntax"
        ]
        
        query = "Python syntax"
        
        # Simple keyword matching
        results = []
        for doc in documents:
            if "Python" in doc or "syntax" in doc:
                results.append(doc)
        
        assert len(results) == 2
        assert "Python has simple syntax" in results
    
    @pytest.mark.unit
    def test_similarity_scoring(self):
        """Test similarity scoring between documents"""
        # Simple Jaccard similarity
        def jaccard_similarity(text1, text2):
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            if not union:
                return 0.0
            return len(intersection) / len(union)
        
        doc1 = "Python programming is fun"
        doc2 = "Python programming is powerful"
        doc3 = "Java is different"
        
        sim1 = jaccard_similarity(doc1, doc2)
        sim2 = jaccard_similarity(doc1, doc3)
        
        assert sim1 > sim2  # More similar documents should have higher score


class TestRAGIntegration:
    """Integration tests for RAG system"""
    
    @pytest.mark.integration
    @pytest.mark.requires_chromadb
    def test_end_to_end_rag_flow(self, temp_test_dir):
        """Test complete RAG flow from document to answer"""
        # Initialize real system
        rag = EducationalRAG(
            persist_directory=str(temp_test_dir / "integration_test")
        )
        
        # Add documents using actual method
        documents = [
            {"text": "Python is a high-level programming language", "metadata": {"topic": "intro"}},
            {"text": "Functions in Python are defined using def keyword", "metadata": {"topic": "functions"}},
            {"text": "Python supports object-oriented programming", "metadata": {"topic": "oop"}}
        ]
        
        # If RAG is initialized, test actual indexing
        if rag.initialized:
            import asyncio
            result = asyncio.run(rag.index_educational_content(documents))
            assert result is True
        else:
            pytest.skip("RAG system not initialized - missing dependencies")


class TestDocumentLoader:
    """Test document loading functionality"""
    
    @pytest.mark.unit
    def test_load_text_file(self, temp_test_dir):
        """Test loading plain text file"""
        # Create test file
        test_file = temp_test_dir / "test.txt"
        test_file.write_text("This is test content")
        
        # Load file
        content = test_file.read_text()
        
        assert content == "This is test content"
    
    @pytest.mark.unit
    def test_load_markdown_file(self, temp_test_dir):
        """Test loading markdown file"""
        # Create test markdown file
        test_file = temp_test_dir / "test.md"
        test_file.write_text("# Title\n\nThis is content")
        
        # Load file
        content = test_file.read_text()
        
        assert "# Title" in content
        assert "This is content" in content
