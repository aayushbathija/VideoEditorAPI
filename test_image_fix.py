#!/usr/bin/env python3
"""
Test script for the image voiceover fix verification.
Creates local test files to validate functionality.
"""

import requests
import json
import time
import os
from PIL import Image
import numpy as np

# Create a simple test image
def create_test_image():
    """Create a simple test PNG image."""
    # Create a simple colored image
    width, height = 800, 600
    image_array = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Create a simple gradient pattern
    for y in range(height):
        for x in range(width):
            image_array[y, x] = [x % 256, y % 256, (x + y) % 256]
    
    # Save as PNG
    image = Image.fromarray(image_array)
    image.save('/tmp/test_image.png')
    print("Created test image: /tmp/test_image.png")
    return '/tmp/test_image.png'

# Create a simple test audio (silence)  
def create_test_audio():
    """Create a simple test WAV file."""
    try:
        import wave
        import struct
        
        # Create 2 seconds of silence
        sample_rate = 44100
        duration = 2.0
        num_samples = int(sample_rate * duration)
        
        with wave.open('/tmp/test_audio.wav', 'w') as wav_file:
            wav_file.setnchannels(1)  # mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            
            # Write silence (zeros)
            for _ in range(num_samples):
                wav_file.writeframes(struct.pack('<h', 0))
        
        print("Created test audio: /tmp/test_audio.wav")
        return '/tmp/test_audio.wav'
    except ImportError:
        print("Wave module not available, using alternative method")
        # Create a minimal WAV file manually
        with open('/tmp/test_audio.wav', 'wb') as f:
            # WAV header for 1 second of silence
            f.write(b'RIFF')
            f.write((44100 * 2 + 36).to_bytes(4, 'little'))  # File size
            f.write(b'WAVE')
            f.write(b'fmt ')
            f.write((16).to_bytes(4, 'little'))  # Format chunk size
            f.write((1).to_bytes(2, 'little'))   # Audio format (PCM)
            f.write((1).to_bytes(2, 'little'))   # Number of channels
            f.write((44100).to_bytes(4, 'little'))  # Sample rate
            f.write((88200).to_bytes(4, 'little'))  # Byte rate
            f.write((2).to_bytes(2, 'little'))   # Block align
            f.write((16).to_bytes(2, 'little'))  # Bits per sample
            f.write(b'data')
            f.write((44100 * 2).to_bytes(4, 'little'))  # Data chunk size
            
            # Write 1 second of silence
            for _ in range(44100):
                f.write(b'\x00\x00')  # 16-bit silence
        
        return '/tmp/test_audio.wav'

def test_image_voiceover():
    """Test the image voiceover functionality."""
    print("Testing Image Voiceover Fix...")
    
    # Create test files
    image_path = create_test_image()
    audio_path = create_test_audio()
    
    # Test with local file URLs
    test_data = {
        "image_url": f"file://{image_path}",
        "audio_url": f"file://{audio_path}",
        "zoom_factor": 1.1
    }
    
    print(f"\nTesting with:")
    print(f"Image: {test_data['image_url']}")
    print(f"Audio: {test_data['audio_url']}")
    print(f"Zoom: {test_data['zoom_factor']}")
    
    # Submit job
    try:
        response = requests.post(
            "http://localhost:8080/add-voiceover",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 202:
            job_info = response.json()
            job_id = job_info['job_id']
            print(f"\n✅ Job submitted: {job_id}")
            
            # Monitor progress
            for i in range(60):  # Wait up to 60 seconds
                status_response = requests.get(f"http://localhost:8080/job-status/{job_id}")
                
                if status_response.status_code == 200:
                    status = status_response.json()
                    print(f"Progress: {status.get('progress', 0)}% - {status.get('status_message', 'Processing...')}")
                    
                    if status['status'] == 'completed':
                        print("🎉 SUCCESS! Image voiceover processing completed!")
                        print(f"Output: {status.get('output_path', 'N/A')}")
                        return True
                    elif status['status'] == 'failed':
                        print(f"❌ FAILED: {status.get('error', 'Unknown error')}")
                        return False
                
                time.sleep(2)
            
            print("⏰ Timeout waiting for completion")
            return False
        else:
            print(f"❌ Job submission failed: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        # Cleanup test files
        for path in [image_path, audio_path]:
            try:
                os.remove(path)
                print(f"Cleaned up: {path}")
            except:
                pass

def main():
    print("Image Voiceover Fix Verification")
    print("=" * 40)
    
    # Check if server is running
    try:
        health = requests.get("http://localhost:8080/health", timeout=5)
        if health.status_code != 200:
            print("❌ Server not healthy")
            return False
        print("✅ Server is healthy")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return False
    
    # Run test
    success = test_image_voiceover()
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
        print("The image voiceover fix is working correctly.")
    else:
        print("\n❌ TESTS FAILED!")
        print("There may still be issues with the implementation.")
    
    return success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)