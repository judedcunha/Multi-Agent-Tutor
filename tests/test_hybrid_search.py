"""
Test Script for True Hybrid Search Implementation
Demonstrates BM25 + Semantic Search capabilities
"""

import asyncio
import sys
import os
# Add src directory to path
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from rag.educational_retrieval import create_rag_system
from colorama import Fore, Style, init

# Initialize colorama for colored output
init(autoreset=True)

async def main():
    """Test the new hybrid search implementation"""
    
    print(f"{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}True Hybrid Search Test Suite")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    # Create RAG system
    print(f"{Fore.YELLOW}Initializing RAG system...")
    rag, reranker = create_rag_system(
        persist_directory="./test_chroma_db",
        collection_name="test_educational_content"
    )
    
    if not rag.initialized:
        print(f"{Fore.RED}RAG system not initialized!")
        print(f"{Fore.RED}Please install required packages:")
        print(f"{Fore.RED}pip install chromadb sentence-transformers rank-bm25")
        return
    
    # Check capabilities
    stats = await rag.get_search_statistics()
    print(f"\n{Fore.GREEN}System Initialized Successfully!")
    print(f"\n{Fore.CYAN}System Capabilities:")
    print(f"  {'✅' if stats['chromadb_initialized'] else '❌'} ChromaDB Vector Search")
    print(f"  {'✅' if stats['bm25_initialized'] else '❌'} BM25 Keyword Search")
    print(f"  {'✅' if stats['hybrid_search_available'] else '❌'} Hybrid Search")
    print(f"  {'✅' if stats['embedder_available'] else '❌'} Sentence Embeddings")
    print(f"  {'✅' if reranker.initialized else '❌'} Cross-Encoder Reranking")
    
    # Comprehensive test corpus
    test_corpus = [
        # Python Programming
        {
            'id': 'python_1',
            'text': 'Python is a high-level programming language known for its simple syntax. Python uses indentation to define code blocks instead of curly braces. The print() function displays output to the console.',
            'metadata': {'subject': 'programming', 'level': 'beginner', 'language': 'python'}
        },
        {
            'id': 'python_2',
            'text': 'Lists in Python are mutable sequences that can hold multiple items. You can use append() to add items and pop() to remove them. List comprehensions provide a concise way to create lists.',
            'metadata': {'subject': 'programming', 'level': 'beginner', 'language': 'python'}
        },
        {
            'id': 'python_3',
            'text': 'Object-oriented programming in Python uses classes and objects. Classes define blueprints for objects with attributes and methods. Inheritance allows classes to inherit properties from parent classes.',
            'metadata': {'subject': 'programming', 'level': 'intermediate', 'language': 'python'}
        },
        {
            'id': 'python_4',
            'text': 'Decorators in Python are functions that modify other functions. They use the @ symbol and can add functionality like logging or timing. Advanced decorators can accept arguments and maintain state.',
            'metadata': {'subject': 'programming', 'level': 'advanced', 'language': 'python'}
        },
        
        # Mathematics
        {
            'id': 'math_1',
            'text': 'Linear equations have the form ax + b = c where a, b, and c are constants. To solve for x, isolate it by performing inverse operations on both sides of the equation.',
            'metadata': {'subject': 'mathematics', 'level': 'beginner', 'topic': 'algebra'}
        },
        {
            'id': 'math_2',
            'text': 'Quadratic equations have the form ax² + bx + c = 0. The quadratic formula x = (-b ± √(b²-4ac))/2a can solve any quadratic equation. The discriminant b²-4ac determines the nature of roots.',
            'metadata': {'subject': 'mathematics', 'level': 'intermediate', 'topic': 'algebra'}
        },
        {
            'id': 'math_3',
            'text': 'Derivatives measure the rate of change of functions. The power rule states that the derivative of x^n is nx^(n-1). Chain rule is used for composite functions.',
            'metadata': {'subject': 'mathematics', 'level': 'advanced', 'topic': 'calculus'}
        },
        
        # Data Science
        {
            'id': 'ds_1',
            'text': 'Pandas DataFrames are two-dimensional data structures in Python. You can load data from CSV files using pd.read_csv(). DataFrames support operations like filtering, grouping, and merging.',
            'metadata': {'subject': 'data_science', 'level': 'intermediate', 'library': 'pandas'}
        },
        {
            'id': 'ds_2',
            'text': 'Machine learning models learn patterns from data. Supervised learning uses labeled data for training. Common algorithms include linear regression, decision trees, and neural networks.',
            'metadata': {'subject': 'data_science', 'level': 'intermediate', 'topic': 'ml'}
        }
    ]
    
    # Index the corpus
    print(f"\n{Fore.YELLOW}Indexing {len(test_corpus)} documents...")
    success = await rag.index_educational_content(test_corpus)
    if success:
        print(f"{Fore.GREEN}✅ Successfully indexed all documents\n")
    else:
        print(f"{Fore.RED}❌ Failed to index documents\n")
        return
    
    # Test queries with different characteristics
    test_queries = [
        {
            'query': 'How to use append and pop methods with Python lists?',
            'description': 'Exact keyword match query'
        },
        {
            'query': 'What are mutable sequences in programming?',
            'description': 'Semantic understanding query'
        },
        {
            'query': 'quadratic formula discriminant roots',
            'description': 'Technical terms query'
        },
        {
            'query': 'How do decorators work in Python programming?',
            'description': 'Mixed semantic and keyword query'
        },
        {
            'query': 'data manipulation with pandas dataframes CSV files',
            'description': 'Domain-specific query'
        }
    ]
    
    print(f"{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}🔬 Running Search Comparison Tests")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    for test_case in test_queries:
        query = test_case['query']
        description = test_case['description']
        
        print(f"{Fore.MAGENTA}Query: '{query}'")
        print(f"{Fore.MAGENTA}   Type: {description}\n")
        
        # Run all search methods
        semantic_results = await rag.semantic_search(query, top_k=3)
        keyword_results = await rag.keyword_search(query, top_k=3)
        hybrid_weighted = await rag.hybrid_search(
            query, top_k=3, 
            semantic_weight=0.6, 
            bm25_weight=0.4,
            fusion_method="weighted"
        )
        hybrid_rrf = await rag.hybrid_search(
            query, top_k=3,
            fusion_method="rrf"
        )
        
        # Display results comparison
        print(f"{Fore.YELLOW}  Semantic Search (Top 3):")
        for i, res in enumerate(semantic_results[:3], 1):
            print(f"    {i}. [{res['score']:.3f}] {res['content'][:60]}...")
        
        print(f"\n{Fore.YELLOW}  BM25 Keyword Search (Top 3):")
        for i, res in enumerate(keyword_results[:3], 1):
            raw_score = f" (Raw: {res.get('bm25_raw_score', 0):.2f})" if 'bm25_raw_score' in res else ""
            print(f"    {i}. [{res['score']:.3f}{raw_score}] {res['content'][:60]}...")
        
        print(f"\n{Fore.GREEN}  Hybrid Search - Weighted (Top 3):")
        for i, res in enumerate(hybrid_weighted[:3], 1):
            sources = '/'.join(res.get('sources', ['?']))
            print(f"    {i}. [{res['combined_score']:.3f}] [{sources}] {res['content'][:60]}...")
        
        print(f"\n{Fore.GREEN}  Hybrid Search - RRF (Top 3):")
        for i, res in enumerate(hybrid_rrf[:3], 1):
            sources = '/'.join(res.get('sources', ['?']))
            rrf_score = f" RRF:{res.get('rrf_score', 0):.4f}" if 'rrf_score' in res else ""
            print(f"    {i}. [{res['combined_score']:.3f}]{rrf_score} [{sources}] {res['content'][:60]}...")
        
        # Rerank if available
        if reranker.initialized and hybrid_weighted:
            print(f"\n{Fore.CYAN}  Re-ranked Results (Cross-Encoder):")
            reranked = reranker.rerank_for_learning(hybrid_weighted, query, top_k=3)
            for i, res in enumerate(reranked[:3], 1):
                print(f"    {i}. [{res['rerank_score']:.3f}] {res['content'][:60]}...")
        
        print(f"\n{Fore.CYAN}{'-'*70}\n")
    
    # Performance comparison
    print(f"{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}Performance Analysis")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    # Test query for performance comparison
    perf_query = "How to solve quadratic equations using Python?"
    
    print(f"{Fore.YELLOW}Testing query: '{perf_query}'\n")
    
    # Measure which sources contribute to hybrid results
    hybrid_results = await rag.hybrid_search(perf_query, top_k=5)
    
    semantic_only = sum(1 for r in hybrid_results if r.get('sources') == ['semantic'])
    bm25_only = sum(1 for r in hybrid_results if r.get('sources') == ['bm25'])
    both_sources = sum(1 for r in hybrid_results if len(r.get('sources', [])) == 2)
    
    print(f"{Fore.GREEN}Result Source Distribution (Top 5):")
    print(f"  • Semantic only: {semantic_only}")
    print(f"  • BM25 only: {bm25_only}")
    print(f"  • Both sources: {both_sources}")
    
    # Show score distributions
    print(f"\n{Fore.GREEN}Score Distribution:")
    for i, res in enumerate(hybrid_results[:5], 1):
        sources = res.get('sources', [])
        semantic_score = res.get('semantic_score', 0)
        bm25_score = res.get('bm25_score', 0)
        combined_score = res.get('combined_score', 0)
        
        print(f"  {i}. Combined: {combined_score:.3f}")
        if 'semantic' in sources:
            print(f"     - Semantic: {semantic_score:.3f}")
        if 'bm25' in sources:
            print(f"     - BM25: {bm25_score:.3f}")
    
    # Test with filters
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}Filtered Search Tests")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    print(f"{Fore.YELLOW}Query: 'Python programming concepts'")
    print(f"Filter: subject='programming', level='beginner'\n")
    
    filtered_results = await rag.hybrid_search(
        "Python programming concepts",
        subject="programming",
        student_level="beginner",
        top_k=3
    )
    
    print(f"{Fore.GREEN}Filtered Results:")
    for i, res in enumerate(filtered_results, 1):
        metadata = res.get('metadata', {})
        print(f"  {i}. [{metadata.get('level')}] {res['content'][:70]}...")
    
    # Final statistics
    final_stats = await rag.get_search_statistics()
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}Final Statistics")
    print(f"{Fore.CYAN}{'='*70}\n")
    print(f"{Fore.GREEN}  Total documents indexed: {final_stats['total_documents']}")
    print(f"{Fore.GREEN}  ChromaDB documents: {final_stats.get('chromadb_document_count', 'N/A')}")
    print(f"{Fore.GREEN}  Hybrid search available: {'Yes' if final_stats['hybrid_search_available'] else 'No'}")
    
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.GREEN}All tests completed successfully!")
    print(f"{Fore.CYAN}{'='*70}\n")

if __name__ == "__main__":
    # Check for required packages
    try:
        import chromadb
        import sentence_transformers
        from rank_bm25 import BM25Okapi
        from colorama import Fore, Style
    except ImportError as e:
        print("Missing required packages. Please install:")
        print("pip install chromadb sentence-transformers rank-bm25 colorama")
        print(f"Error: {e}")
        sys.exit(1)
    
    # Run the test
    asyncio.run(main())
