#!/usr/bin/env python3
"""
Test diagnostic script - checks which tests can run
"""

import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

def check_imports():
    """Check which modules can be imported"""
    modules_to_check = [
        "agents.tutoring_graph",
        "agents.state_schema",
        "agents.ai_tutor",
        "agents.educational_nodes",
        "agents.subject_experts",
        "database.educational_models",
        "database.educational_crud",
        "database.db_manager",
        "llm.educational_clients",
        "optimization.educational_caching",
        "optimization.cache_decorators",
        "rag.educational_retrieval",
        "api.websocket_server",
        "monitoring.educational_analytics",
        "monitoring.langsmith_integration"
    ]
    
    print("🔍 Checking module imports:\n")
    
    available = []
    missing = []
    
    for module in modules_to_check:
        try:
            __import__(module)
            print(f"  ✅ {module}")
            available.append(module)
        except ImportError as e:
            print(f"  ❌ {module}: {str(e)}")
            missing.append(module)
    
    print(f"\n📊 Summary:")
    print(f"  Available modules: {len(available)}/{len(modules_to_check)}")
    print(f"  Missing modules: {len(missing)}/{len(modules_to_check)}")
    
    return available, missing

def run_safe_tests():
    """Run only tests that should work"""
    print("\n🧪 Running safe tests...\n")
    
    # Try to run unit tests only
    result = subprocess.run(
        ["pytest", "-v", "-m", "unit", "--tb=short"],
        capture_output=False,
        cwd=PROJECT_ROOT
    )
    
    return result.returncode

if __name__ == "__main__":
    print("=" * 60)
    print("Multi-Agent Tutor Test Diagnostics")
    print("=" * 60)
    
    available, missing = check_imports()
    
    if available:
        print("\n✨ Some modules are available, attempting to run tests...")
        exit_code = run_safe_tests()
        
        if exit_code == 0:
            print("\n✅ Tests passed!")
        else:
            print(f"\n⚠️  Some tests failed with exit code: {exit_code}")
    else:
        print("\n❌ No modules could be imported. Check your project structure.")
    
    if missing:
        print("\n📝 To fix missing modules:")
        print("  1. Check if the module files exist in src/")
        print("  2. Verify the class/function names match")
        print("  3. Ensure __init__.py files exist in directories")
        print("  4. Check for circular imports")
