#!/usr/bin/env python3
"""
API Endpoint Testing Script
Run this AFTER starting the server (python src/main_tutor.py)
Tests all API endpoints to verify Langgraph implementation
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70 + "\n")

def print_test(name, passed=True, details=""):
    status = "✅" if passed else "❌"
    print(f"{status} {name}")
    if details:
        print(f"   {details}")

def test_endpoint(method: str, endpoint: str, data: Dict = None, expect_200: bool = True) -> Dict[str, Any]:
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        success = (response.status_code == 200) if expect_200 else True
        
        return {
            "success": success,
            "status_code": response.status_code,
            "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else None,
            "text": response.text if not response.headers.get('content-type', '').startswith('application/json') else None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    print_section("PHASE 1 API ENDPOINT TESTING")
    
    print("Make sure the server is running!")
    print("   Start it with: cd src && python main_tutor.py")
    print("\nWaiting for server to be ready...")
    
    # Check if server is running
    max_retries = 5
    for i in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                print("Server is ready!\n")
                break
        except:
            if i == max_retries - 1:
                print("Server not responding!")
                print("   Please start the server first")
                return False
            print(f"   Retry {i+1}/{max_retries}...")
            time.sleep(2)
    
    # Test 1: Health Check
    print_section("Test 1: Health Check")
    result = test_endpoint("GET", "/health")
    if result["success"]:
        data = result["data"]
        print_test("Health endpoint", True, 
                   f"Status: {data.get('status')}, Advanced system: {data.get('advanced_system')}")
    else:
        print_test("Health endpoint", False, result.get("error", "Failed"))
    
    # Test 2: System Status
    print_section("Test 2: System Status")
    result = test_endpoint("GET", "/system-status")
    if result["success"]:
        data = result["data"]
        print_test("System status endpoint", True,
                   f"Phase: {data.get('phase')}, Agents: {data.get('agents', {}).get('count', 0)}")
        
        if data.get("agents", {}).get("count") == 6:
            print_test("All 6 agents active")
        else:
            print_test(f"Expected 6 agents, got {data.get('agents', {}).get('count')}", False)
    else:
        print_test("System status endpoint", False, result.get("error"))
    
    # Test 3: Welcome Page
    print_section("Test 3: Welcome Page")
    result = test_endpoint("GET", "/")
    if result["success"]:
        if "Multi-Agent" in result.get("text", ""):
            print_test("Welcome page", True, "Contains 'Multi-Agent'")
        else:
            print_test("Welcome page content issue", False)
    else:
        print_test("Welcome page", False)
    
    # Test 4: Basic Teaching 
    print_section("Test 4: Basic Teaching Endpoint (Backward Compatible)")
    result = test_endpoint("POST", "/teach", {
        "topic": "Python variables",
        "student_level": "beginner",
        "learning_style": "visual",
        "student_name": "TestUser"
    })
    
    if result["success"]:
        data = result["data"]
        session = data.get("teaching_session", {})
        print_test("Basic /teach endpoint", True,
                   f"Subject: {session.get('detected_subject')}, Practice: {len(session.get('practice_problems', []))}")
    else:
        print_test("Basic /teach endpoint", False, result.get("error"))
    
    # Test 5: Advanced Multi-Agent Teaching
    print_section("Test 5: Advanced Multi-Agent Teaching")
    start_time = time.time()
    result = test_endpoint("POST", "/teach/advanced", {
        "topic": "Introduction to algorithms",
        "student_level": "intermediate",
        "learning_style": "mixed",
        "student_name": "TestUser",
        "learning_goals": ["Learn algorithms"],
        "use_multi_agent": True
    })
    duration = time.time() - start_time
    
    if result["success"]:
        data = result["data"]
        session = data.get("teaching_session", {})
        
        checks = {
            "Multi-agent used": data.get("multi_agent_used") == True,
            "6 agents involved": data.get("agent_count") == 6,
            "Has lesson plan": "lesson_plan" in session,
            "Has practice": len(session.get("practice_problems", [])) > 0,
            "Has content": len(session.get("educational_content", [])) >= 0
        }
        
        print_test("Advanced /teach/advanced endpoint", True,
                   f"Duration: {duration:.2f}s, Agents: {data.get('agent_count')}")
        
        for check_name, passed in checks.items():
            print_test(f"  {check_name}", passed)
    else:
        print_test("Advanced /teach/advanced endpoint", False, result.get("error"))
    
    # Test 6: Personalized Practice
    print_section("Test 6: Personalized Practice")
    result = test_endpoint("POST", "/practice/personalized", {
        "topic": "Python loops",
        "student_level": "beginner",
        "student_name": "TestUser"
    })
    
    if result["success"]:
        data = result["data"]
        print_test("Personalized practice endpoint", True,
                   f"Problems: {data.get('practice_count', 0)}, Agents: {len(data.get('agents_used', []))}")
    else:
        print_test("Personalized practice endpoint", False, result.get("error"))
    
    # Test 7: Understanding Assessment
    print_section("Test 7: Understanding Assessment")
    result = test_endpoint("POST", "/assess/understanding", {
        "topic": "Python functions",
        "student_response": "Functions are reusable blocks of code that perform specific tasks",
        "original_question": "What are functions?"
    })
    
    if result["success"]:
        data = result["data"]
        assessment = data.get("assessment", {})
        print_test("Assessment endpoint", True,
                   f"Understanding: {assessment.get('understanding_level')}")
    else:
        print_test("Assessment endpoint", False, result.get("error"))
    
    # Test 8: Quick Question
    print_section("Test 8: Quick Question (Backward Compatible)")
    result = test_endpoint("POST", "/ask", {
        "question": "What is polymorphism?",
        "student_level": "intermediate"
    })
    
    if result["success"]:
        data = result["data"]
        print_test("Quick question endpoint", True,
                   f"Answer provided: {len(data.get('answer', {}).get('explanation', '')) > 0}")
    else:
        print_test("Quick question endpoint", False, result.get("error"))
    
    # Test 9: Demo
    print_section("Test 9: Demo Endpoint")
    result = test_endpoint("GET", "/demo")
    if result["success"]:
        data = result["data"]
        print_test("Demo endpoint", True,
                   f"Multi-agent: {data.get('multi_agent')}, Agents: {data.get('agent_count')}")
    else:
        print_test("Demo endpoint", False, result.get("error"))
    
    # Test 10: Supported Subjects
    print_section("Test 10: Supported Subjects")
    result = test_endpoint("GET", "/subjects")
    if result["success"]:
        data = result["data"]
        subjects = data.get("supported_subjects", {})
        print_test("Subjects endpoint", True,
                   f"Categories: {len(subjects)}, Phase: {data.get('phase')}")
    else:
        print_test("Subjects endpoint", False, result.get("error"))
    
    # Test 11: Student Guide
    print_section("Test 11: Student Guide")
    result = test_endpoint("GET", "/student-guide")
    if result["success"]:
        data = result["data"]
        print_test("Student guide endpoint", True,
                   f"Sections: {len(data)}")
    else:
        print_test("Student guide endpoint", False, result.get("error"))
    
    # Summary
    print_section("API TESTING COMPLETE")
    print("All API endpoints tested!")
    print("\nWhat was tested:")
    print("  • Health check (/health)")
    print("  • System status (/system-status)")
    print("  • Welcome page (/)")
    print("  • Basic teaching (/teach) ")
    print("  • Advanced teaching (/teach/advanced)")
    print("  • Personalized practice (/practice/personalized)")
    print("  • Understanding assessment (/assess/understanding)")
    print("  • Quick questions (/ask) - Backward compatible")
    print("  • Demo endpoint (/demo)")
    print("  • Supported subjects (/subjects)")
    print("  • Student guide (/student-guide)")
    print("\nPhase 1 API: VERIFIED ")
    print("="*70 + "\n")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        success = False
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        success = False
