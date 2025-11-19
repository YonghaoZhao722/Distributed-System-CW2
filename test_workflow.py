#!/usr/bin/env python3
"""
Workflow Performance and Scalability Test Script
Tests HTTP → SQL → SQL Trigger workflow with different loads
"""

import requests
import time
import json
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import os

# Configuration
BASE_URL = "http://localhost:7071/api/HttpTrigger"
RESULTS_DIR = "test_results"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Create results directory
os.makedirs(RESULTS_DIR, exist_ok=True)

def get_system_info():
    """Get system information"""
    return {
        "cpu_count": psutil.cpu_count(),
        "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
        "memory_total_gb": psutil.virtual_memory().total / (1024**3),
        "platform": sys.platform,
        "python_version": sys.version,
    }

def send_request(task_id, payload, max_retries=2):
    """Send a single HTTP request with retry logic"""
    start_time = time.time()
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                BASE_URL,
                json={"task": payload},
                headers={"Content-Type": "application/json"},
                timeout=60  # Increased timeout for high load scenarios
            )
            end_time = time.time()
            duration = (end_time - start_time) * 1000  # Convert to ms
            
            success = response.status_code == 200
            
            result = {
                "task_id": task_id,
                "status_code": response.status_code,
                "duration_ms": duration,
                "success": success,
                "response": response.text[:200],  # Truncate long responses
                "attempt": attempt + 1,
                "timestamp": datetime.now().isoformat()
            }
            
            # If successful or non-retryable error (4xx), return immediately
            if success or (400 <= response.status_code < 500):
                return result
            
            # For 5xx errors, retry if attempts remain
            if attempt < max_retries - 1:
                time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                continue
            
            return result
            
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(0.5 * (attempt + 1))
                continue
            end_time = time.time()
            duration = (end_time - start_time) * 1000
            return {
                "task_id": task_id,
                "status_code": None,
                "duration_ms": duration,
                "success": False,
                "error": "Request timeout",
                "attempt": attempt + 1,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(0.5 * (attempt + 1))
                continue
            end_time = time.time()
            duration = (end_time - start_time) * 1000
            return {
                "task_id": task_id,
                "status_code": None,
                "duration_ms": duration,
                "success": False,
                "error": str(e)[:200],  # Truncate long error messages
                "attempt": attempt + 1,
                "timestamp": datetime.now().isoformat()
            }

def test_single_request():
    """Test Case 6: Single request performance"""
    print("\n" + "="*60)
    print("Test Case 6: Single Request Performance")
    print("="*60)
    
    # Monitor system resources
    cpu_before = psutil.cpu_percent(interval=0.1)
    memory_before = psutil.virtual_memory().percent
    
    result = send_request(1, f"test_single_{TIMESTAMP}")
    
    cpu_after = psutil.cpu_percent(interval=0.1)
    memory_after = psutil.virtual_memory().percent
    
    metrics = {
        "test_case": "single_request",
        "n": 1,
        "results": [result],
        "system_metrics": {
            "cpu_before": cpu_before,
            "cpu_after": cpu_after,
            "memory_before": memory_before,
            "memory_after": memory_after,
        },
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"Status: {result['status_code']}")
    print(f"Duration: {result['duration_ms']:.2f} ms")
    print(f"CPU: {cpu_before:.1f}% → {cpu_after:.1f}%")
    print(f"Memory: {memory_before:.1f}% → {memory_after:.1f}%")
    
    return metrics

def test_medium_load(n=50):
    """Test Case 8: Medium load (N=50)"""
    print("\n" + "="*60)
    print(f"Test Case 8: Medium Load (N={n})")
    print("="*60)
    
    cpu_before = psutil.cpu_percent(interval=0.1)
    memory_before = psutil.virtual_memory().percent
    
    start_time = time.time()
    results = []
    
    # Send requests concurrently (1 second window)
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(send_request, i+1, f"test_medium_{TIMESTAMP}_{i+1}")
            for i in range(n)
        ]
        
        for future in as_completed(futures):
            results.append(future.result())
    
    end_time = time.time()
    total_duration = (end_time - start_time) * 1000
    
    cpu_after = psutil.cpu_percent(interval=0.1)
    memory_after = psutil.virtual_memory().percent
    
    successful = sum(1 for r in results if r['success'])
    avg_duration = sum(r['duration_ms'] for r in results) / len(results) if results else 0
    
    metrics = {
        "test_case": "medium_load",
        "n": n,
        "total_duration_ms": total_duration,
        "successful_requests": successful,
        "failed_requests": n - successful,
        "avg_duration_ms": avg_duration,
        "results": results,
        "system_metrics": {
            "cpu_before": cpu_before,
            "cpu_after": cpu_after,
            "memory_before": memory_before,
            "memory_after": memory_after,
        },
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"Total Duration: {total_duration:.2f} ms")
    print(f"Successful: {successful}/{n}")
    print(f"Average Duration: {avg_duration:.2f} ms")
    print(f"CPU: {cpu_before:.1f}% → {cpu_after:.1f}%")
    print(f"Memory: {memory_before:.1f}% → {memory_after:.1f}%")
    
    return metrics

def test_high_load(n=200):
    """Test Case 9: High load (N=200+)"""
    print("\n" + "="*60)
    print(f"Test Case 9: High Load (N={n})")
    print("="*60)
    
    cpu_before = psutil.cpu_percent(interval=0.1)
    memory_before = psutil.virtual_memory().percent
    
    start_time = time.time()
    results = []
    
    # Send requests with controlled concurrency
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(send_request, i+1, f"test_high_{TIMESTAMP}_{i+1}")
            for i in range(n)
        ]
        
        completed = 0
        for future in as_completed(futures):
            results.append(future.result())
            completed += 1
            if completed % 50 == 0:
                print(f"Progress: {completed}/{n} requests completed")
    
    end_time = time.time()
    total_duration = (end_time - start_time) * 1000
    
    cpu_after = psutil.cpu_percent(interval=0.1)
    memory_after = psutil.virtual_memory().percent
    
    successful = sum(1 for r in results if r['success'])
    avg_duration = sum(r['duration_ms'] for r in results) / len(results) if results else 0
    durations = [r['duration_ms'] for r in results if r['success']]
    min_duration = min(durations) if durations else 0
    max_duration = max(durations) if durations else 0
    
    metrics = {
        "test_case": "high_load",
        "n": n,
        "total_duration_ms": total_duration,
        "successful_requests": successful,
        "failed_requests": n - successful,
        "avg_duration_ms": avg_duration,
        "min_duration_ms": min_duration,
        "max_duration_ms": max_duration,
        "results": results,
        "system_metrics": {
            "cpu_before": cpu_before,
            "cpu_after": cpu_after,
            "memory_before": memory_before,
            "memory_after": memory_after,
        },
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"Total Duration: {total_duration:.2f} ms ({total_duration/1000:.2f} seconds)")
    print(f"Successful: {successful}/{n}")
    print(f"Average Duration: {avg_duration:.2f} ms")
    print(f"Min Duration: {min_duration:.2f} ms")
    print(f"Max Duration: {max_duration:.2f} ms")
    print(f"CPU: {cpu_before:.1f}% → {cpu_after:.1f}%")
    print(f"Memory: {memory_before:.1f}% → {memory_after:.1f}%")
    
    return metrics

def test_functional():
    """Test Case 1-2: Functional tests"""
    print("\n" + "="*60)
    print("Test Case 1-2: Functional Tests")
    print("="*60)
    
    results = []
    for i in range(5):
        print(f"Sending request {i+1}/5...")
        result = send_request(i+1, f"functional_test_{TIMESTAMP}_{i+1}")
        results.append(result)
        time.sleep(0.5)  # Small delay between requests
    
    successful = sum(1 for r in results if r['success'])
    print(f"\nFunctional Test Results: {successful}/5 successful")
    
    return {
        "test_case": "functional",
        "n": 5,
        "successful": successful,
        "results": results,
        "timestamp": datetime.now().isoformat()
    }

def main():
    """Run all tests"""
    print("="*60)
    print("Workflow Performance and Scalability Test Suite")
    print(f"Timestamp: {TIMESTAMP}")
    print("="*60)
    
    # Get system info
    system_info = get_system_info()
    print("\nSystem Information:")
    print(json.dumps(system_info, indent=2))
    
    # Save system info
    with open(f"{RESULTS_DIR}/system_info_{TIMESTAMP}.json", "w") as f:
        json.dump(system_info, f, indent=2)
    
    all_results = {
        "system_info": system_info,
        "timestamp": TIMESTAMP,
        "tests": []
    }
    
    # Run tests
    try:
        # Functional tests
        func_results = test_functional()
        all_results["tests"].append(func_results)
        
        # Wait a bit between test suites
        print("\nWaiting 5 seconds before performance tests...")
        time.sleep(5)
        
        # Single request
        single_results = test_single_request()
        all_results["tests"].append(single_results)
        
        # Wait between tests
        print("\nWaiting 5 seconds before medium load test...")
        time.sleep(5)
        
        # Medium load
        medium_results = test_medium_load(50)
        all_results["tests"].append(medium_results)
        
        # Wait between tests
        print("\nWaiting 10 seconds before high load test...")
        time.sleep(10)
        
        # High load
        high_results = test_high_load(200)
        all_results["tests"].append(high_results)
        
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\nError during tests: {e}")
        import traceback
        traceback.print_exc()
    
    # Save all results
    output_file = f"{RESULTS_DIR}/test_results_{TIMESTAMP}.json"
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    
    print("\n" + "="*60)
    print(f"All results saved to: {output_file}")
    print("="*60)
    
    # Print summary
    print("\nTest Summary:")
    for test in all_results["tests"]:
        if "test_case" in test:
            print(f"  {test['test_case']}: ", end="")
            if "successful" in test:
                print(f"{test.get('successful', 0)}/{test.get('n', 0)} successful")
            elif "successful_requests" in test:
                print(f"{test.get('successful_requests', 0)}/{test.get('n', 0)} successful")
            else:
                print("completed")

if __name__ == "__main__":
    main()

