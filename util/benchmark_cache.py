"""
Cache Performance Benchmark Script
Measures cache performance improvements in the Multi-Agent Tutor system
"""

import sys
import os
import time
import asyncio
import statistics
from typing import List, Dict, Any, Callable
import json
import hashlib

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from optimization.educational_caching import cache_manager
from optimization.cache_decorators import cache_result, cache_lesson


class CacheBenchmark:
    """Benchmark cache performance"""
    
    def __init__(self):
        self.results = []
        
    async def benchmark_operation(self, name: str, operation: Callable, 
                                  iterations: int = 100) -> Dict[str, Any]:
        """
        Benchmark a single operation
        
        Args:
            name: Operation name
            operation: Async function to benchmark
            iterations: Number of iterations
            
        Returns:
            Benchmark results
        """
        print(f"\n📊 Benchmarking: {name}")
        print(f"   Iterations: {iterations}")
        
        times = []
        cache_hits = 0
        cache_misses = 0
        
        # Warm up
        await operation()
        
        # Run iterations
        for i in range(iterations):
            start = time.perf_counter()
            result = await operation()
            duration = time.perf_counter() - start
            times.append(duration * 1000)  # Convert to milliseconds
            
            # Track cache hits/misses (simplified detection)
            if duration < 1:  # Assuming cache hits are < 1ms
                cache_hits += 1
            else:
                cache_misses += 1
            
            # Progress indicator
            if (i + 1) % 20 == 0:
                print(f"   Progress: {i + 1}/{iterations}")
        
        # Calculate statistics
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        min_time = min(times)
        max_time = max(times)
        p95_time = statistics.quantiles(times, n=20)[18]  # 95th percentile
        
        result = {
            'name': name,
            'iterations': iterations,
            'avg_time_ms': round(avg_time, 3),
            'median_time_ms': round(median_time, 3),
            'min_time_ms': round(min_time, 3),
            'max_time_ms': round(max_time, 3),
            'p95_time_ms': round(p95_time, 3),
            'cache_hit_rate': round(cache_hits / iterations, 3)
        }
        
        print(f"   ✅ Complete - Avg: {avg_time:.3f}ms, P95: {p95_time:.3f}ms")
        print(f"   Cache hit rate: {result['cache_hit_rate']*100:.1f}%")
        
        return result
    
    async def simulate_lesson_generation(self, use_cache: bool = True) -> Dict:
        """Simulate lesson generation with/without cache"""
        topic = "Python Loops"
        level = "beginner"
        style = "visual"
        
        if use_cache:
            # Check cache
            cached = cache_manager.get_lesson(topic, level, style)
            if cached:
                return cached
            
            # Simulate generation
            await asyncio.sleep(0.1)  # Simulate 100ms generation time
            lesson = {"content": "Generated lesson", "timestamp": time.time()}
            
            # Cache result
            cache_manager.set_lesson(topic, level, style, lesson)
            return lesson
        else:
            # Always generate (no cache)
            await asyncio.sleep(0.1)
            return {"content": "Generated lesson", "timestamp": time.time()}
    
    async def simulate_rag_search(self, use_cache: bool = True) -> List:
        """Simulate RAG search with/without cache"""
        query = "explain recursion"
        subject = "programming"
        level = "intermediate"
        
        if use_cache:
            # Check cache
            cached = cache_manager.get_rag_results(query, subject, level)
            if cached:
                return cached
            
            # Simulate search
            await asyncio.sleep(0.05)  # Simulate 50ms search time
            results = [{"doc": f"Result {i}"} for i in range(5)]
            
            # Cache result
            cache_manager.set_rag_results(query, subject, level, results)
            return results
        else:
            # Always search (no cache)
            await asyncio.sleep(0.05)
            return [{"doc": f"Result {i}"} for i in range(5)]
    
    async def run_comprehensive_benchmark(self):
        """Run comprehensive cache benchmarks"""
        print("\n" + "=" * 60)
        print("CACHE PERFORMANCE BENCHMARK")
        print("=" * 60)
        
        # Initialize cache
        print("\n🔧 Initializing cache system...")
        cache_manager.initialize()
        
        if not cache_manager.enabled:
            print("❌ Cache is not enabled! Redis might not be running.")
            return
        
        # Clear cache for clean benchmark
        cache_manager.clear_cache()
        print("✅ Cache cleared for clean benchmark")
        
        # Benchmark 1: Lesson Generation
        print("\n" + "-" * 60)
        print("Benchmark 1: Lesson Generation")
        print("-" * 60)
        
        # Without cache
        no_cache_lesson = await self.benchmark_operation(
            "Lesson Generation (No Cache)",
            lambda: self.simulate_lesson_generation(use_cache=False),
            iterations=20
        )
        
        # With cache (first run will miss, rest will hit)
        with_cache_lesson = await self.benchmark_operation(
            "Lesson Generation (With Cache)",
            lambda: self.simulate_lesson_generation(use_cache=True),
            iterations=20
        )
        
        # Calculate improvement
        improvement = (no_cache_lesson['avg_time_ms'] - with_cache_lesson['avg_time_ms']) / no_cache_lesson['avg_time_ms'] * 100
        print(f"\n🚀 Performance Improvement: {improvement:.1f}%")
        print(f"   Speedup: {no_cache_lesson['avg_time_ms'] / with_cache_lesson['avg_time_ms']:.1f}x faster")
        
        # Benchmark 2: RAG Search
        print("\n" + "-" * 60)
        print("Benchmark 2: RAG Search")
        print("-" * 60)
        
        # Clear cache for RAG test
        cache_manager.clear_cache("rag")
        
        # Without cache
        no_cache_rag = await self.benchmark_operation(
            "RAG Search (No Cache)",
            lambda: self.simulate_rag_search(use_cache=False),
            iterations=50
        )
        
        # With cache
        with_cache_rag = await self.benchmark_operation(
            "RAG Search (With Cache)",
            lambda: self.simulate_rag_search(use_cache=True),
            iterations=50
        )
        
        # Calculate improvement
        rag_improvement = (no_cache_rag['avg_time_ms'] - with_cache_rag['avg_time_ms']) / no_cache_rag['avg_time_ms'] * 100
        print(f"\n🚀 Performance Improvement: {rag_improvement:.1f}%")
        print(f"   Speedup: {no_cache_rag['avg_time_ms'] / with_cache_rag['avg_time_ms']:.1f}x faster")
        
        # Benchmark 3: Cache Operations
        print("\n" + "-" * 60)
        print("Benchmark 3: Raw Cache Operations")
        print("-" * 60)
        
        # Test raw cache set/get performance
        async def raw_cache_test():
            key = f"test:benchmark:{time.time()}"
            value = {"test": "data", "timestamp": time.time()}
            
            # Set
            start = time.perf_counter()
            cache_manager.redis_client.setex(key, 60, json.dumps(value).encode())
            set_time = (time.perf_counter() - start) * 1000
            
            # Get
            start = time.perf_counter()
            result = cache_manager.redis_client.get(key)
            get_time = (time.perf_counter() - start) * 1000
            
            # Delete
            cache_manager.redis_client.delete(key)
            
            return {'set_time': set_time, 'get_time': get_time}
        
        raw_times = []
        for _ in range(100):
            raw_times.append(await raw_cache_test())
        
        avg_set = statistics.mean([t['set_time'] for t in raw_times])
        avg_get = statistics.mean([t['get_time'] for t in raw_times])
        
        print(f"   Average SET time: {avg_set:.3f}ms")
        print(f"   Average GET time: {avg_get:.3f}ms")
        print(f"   Total round-trip: {avg_set + avg_get:.3f}ms")
        
        # Summary
        print("\n" + "=" * 60)
        print("BENCHMARK SUMMARY")
        print("=" * 60)
        
        print("\n📈 Results Overview:")
        print(f"   Lesson Generation Speedup: {no_cache_lesson['avg_time_ms'] / with_cache_lesson['avg_time_ms']:.1f}x")
        print(f"   RAG Search Speedup: {no_cache_rag['avg_time_ms'] / with_cache_rag['avg_time_ms']:.1f}x")
        print(f"   Cache Hit Rate (Lesson): {with_cache_lesson['cache_hit_rate']*100:.1f}%")
        print(f"   Cache Hit Rate (RAG): {with_cache_rag['cache_hit_rate']*100:.1f}%")
        
        # Get cache stats
        stats = cache_manager.get_cache_stats()
        print(f"\n📊 Cache Statistics:")
        print(f"   Status: {stats.get('status', 'unknown')}")
        print(f"   Total Keys: {stats.get('total_keys', 0)}")
        print(f"   Memory Used: {stats.get('used_memory', 'unknown')}")
        
        # Save results
        self.save_results({
            'lesson_no_cache': no_cache_lesson,
            'lesson_with_cache': with_cache_lesson,
            'rag_no_cache': no_cache_rag,
            'rag_with_cache': with_cache_rag,
            'raw_cache': {
                'avg_set_ms': avg_set,
                'avg_get_ms': avg_get
            },
            'cache_stats': stats
        })
    
    def save_results(self, results: Dict):
        """Save benchmark results to file"""
        from datetime import datetime
        
        filename = f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: {filename}")


async def main():
    """Main benchmark runner"""
    benchmark = CacheBenchmark()
    await benchmark.run_comprehensive_benchmark()


if __name__ == "__main__":
    print("\n🚀 Starting Cache Performance Benchmark...")
    print("This will test cache performance with various operations.")
    print("Make sure Redis is running!\n")
    
    # Check Redis first
    from check_redis import check_redis_connection
    if not check_redis_connection():
        print("\n❌ Redis is not available. Please start Redis first.")
        sys.exit(1)
    
    # Run benchmark
    asyncio.run(main())
