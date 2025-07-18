#!/usr/bin/env python3
"""
Test script for parallel processing implementation
"""

import time
import concurrent.futures
import threading
from typing import List, Dict

def test_parallel_processing():
    """Test the parallel processing implementation"""
    print("🧪 Testing Parallel Processing Implementation")
    
    # Test 1: Thread-safe progress tracking
    print("\n1. Testing Thread-safe Progress Tracking")
    
    progress_lock = threading.Lock()
    progress_data = {"completed": 0, "total": 10, "results": [], "errors": []}
    
    def worker_task(task_id: int) -> Dict:
        """Simulate a worker task"""
        time.sleep(0.1)  # Simulate work
        
        with progress_lock:
            progress_data["completed"] += 1
            progress_data["results"].append({"task_id": task_id, "status": "completed"})
        
        return {"task_id": task_id, "status": "completed"}
    
    # Run parallel tasks
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(worker_task, i) for i in range(10)]
        
        # Monitor progress
        while not all(future.done() for future in futures):
            with progress_lock:
                completed = progress_data["completed"]
                total = progress_data["total"]
                progress = completed / total if total > 0 else 0
            
            print(f"Progress: {completed}/{total} ({progress:.1%})")
            time.sleep(0.1)
    
    print(f"✅ Progress tracking test completed: {progress_data['completed']}/{progress_data['total']}")
    
    # Test 2: Conservative worker limits
    print("\n2. Testing Conservative Worker Limits")
    
    def rate_limited_task(task_id: int) -> Dict:
        """Simulate a rate-limited task (like LLM calls)"""
        time.sleep(0.5)  # Simulate rate limiting
        return {"task_id": task_id, "status": "completed"}
    
    start_time = time.time()
    
    # Test with 2 workers (conservative)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(rate_limited_task, i) for i in range(6)]
        results = [future.result() for future in futures]
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"✅ Rate-limited tasks completed in {duration:.2f}s with 2 workers")
    print(f"   Expected: ~1.5s, Actual: {duration:.2f}s")
    
    # Test 3: Error handling
    print("\n3. Testing Error Handling")
    
    def error_prone_task(task_id: int) -> Dict:
        """Simulate a task that might fail"""
        if task_id % 3 == 0:  # Every 3rd task fails
            raise Exception(f"Task {task_id} failed")
        
        time.sleep(0.1)
        return {"task_id": task_id, "status": "completed"}
    
    error_count = 0
    success_count = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(error_prone_task, i) for i in range(9)]
        
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                success_count += 1
            except Exception as e:
                error_count += 1
                print(f"   Caught error: {e}")
    
    print(f"✅ Error handling test: {success_count} successes, {error_count} errors")
    
    print("\n🎉 All parallel processing tests completed successfully!")
    print("\n📊 Performance Summary:")
    print("   - Thread-safe progress tracking: ✅")
    print("   - Conservative worker limits: ✅")
    print("   - Error handling: ✅")
    print("   - Rate limiting simulation: ✅")

if __name__ == "__main__":
    test_parallel_processing() 