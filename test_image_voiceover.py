#!/usr/bin/env python3
"""
Test script for image-to-video voiceover functionality.
"""

import requests
import time
import json
import sys
import os

# Test configuration
API_BASE_URL = "http://localhost:8080"

# Sample test data - you would replace these with actual URLs
TEST_CASES = [
    {
        "name": "Image with voiceover",
        "description": "Test creating video from image with zoom effect",
        "data": {
            "image_url": "https://sample-videos.com/zip/10/jpg/mp4/SampleJPGImage_30mbmb.jpg",
            "audio_url": "https://sample-videos.com/zip/10/mp3/mp4/SampleAudio_0.4mb_mp3.mp3",
            "zoom_factor": 1.15
        }
    },
    {
        "name": "Video with voiceover (existing functionality)",
        "description": "Test existing video functionality still works",
        "data": {
            "video_url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
            "audio_url": "https://sample-videos.com/zip/10/mp3/mp4/SampleAudio_0.4mb_mp3.mp3",
            "zoom_factor": 1.1
        }
    }
]

def test_endpoint(test_case):
    """Test a single endpoint."""
    print(f"\n{'='*60}")
    print(f"Testing: {test_case['name']}")
    print(f"Description: {test_case['description']}")
    print(f"{'='*60}")
    
    try:
        # Submit job
        print("📤 Submitting job...")
        response = requests.post(f"{API_BASE_URL}/add-voiceover", 
                               json=test_case['data'],
                               headers={'Content-Type': 'application/json'})
        
        if response.status_code != 202:
            print(f"❌ Job submission failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        job_info = response.json()
        job_id = job_info['job_id']
        print(f"✅ Job submitted successfully: {job_id}")
        
        # Monitor job progress
        print("⏳ Monitoring job progress...")
        max_wait = 300  # 5 minutes max
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_response = requests.get(f"{API_BASE_URL}/job-status/{job_id}")
            
            if status_response.status_code != 200:
                print(f"❌ Failed to check job status: {status_response.status_code}")
                return False
            
            status_data = status_response.json()
            print(f"📊 Status: {status_data['status']} | Progress: {status_data.get('progress', 0)}% | {status_data.get('status_message', 'Processing...')}")
            
            if status_data['status'] == 'completed':
                print(f"✅ Job completed successfully!")
                print(f"📁 Output file: {status_data.get('output_path', 'N/A')}")
                
                # Try to download the result
                download_response = requests.get(f"{API_BASE_URL}/download/{job_id}")
                if download_response.status_code == 200:
                    output_filename = f"test_output_{job_id}.mp4"
                    with open(output_filename, 'wb') as f:
                        f.write(download_response.content)
                    print(f"💾 Downloaded result to: {output_filename}")
                
                return True
            
            elif status_data['status'] == 'failed':
                print(f"❌ Job failed: {status_data.get('error', 'Unknown error')}")
                return False
            
            # Wait before next check
            time.sleep(5)
        
        print(f"⏰ Job timed out after {max_wait} seconds")
        return False
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting Image Voiceover Tests")
    print(f"API Base URL: {API_BASE_URL}")
    
    # Check if server is running
    try:
        health_response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if health_response.status_code != 200:
            print(f"❌ Server not healthy: {health_response.status_code}")
            return False
        print("✅ Server is running and healthy")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Make sure the server is running with: python app.py")
        return False
    
    # Run tests
    results = []
    for test_case in TEST_CASES:
        success = test_endpoint(test_case)
        results.append({
            'name': test_case['name'],
            'success': success
        })
    
    # Summary
    print(f"\n{'='*60}")
    print("📋 TEST SUMMARY")
    print(f"{'='*60}")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['success'])
    
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{status}: {result['name']}")
    
    print(f"\nResults: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️ Some tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)