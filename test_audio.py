#!/usr/bin/env python3
"""
Test script to check audio recording functionality.
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from audio.recorder import AudioRecorder

def test_audio_devices():
    """Test audio device detection."""
    print("🎤 Testing audio devices...")
    
    try:
        recorder = AudioRecorder()
        devices = recorder.get_audio_devices()
        
        print(f"Found {len(devices)} audio input devices:")
        for device in devices:
            print(f"  - {device['name']} (Index: {device['index']}, Channels: {device['channels']})")
            
        return len(devices) > 0
        
    except Exception as e:
        print(f"❌ Error detecting audio devices: {e}")
        return False

def test_recording():
    """Test a short recording."""
    print("\n🎙️ Testing recording functionality...")
    
    try:
        recorder = AudioRecorder()
        
        # Start recording
        print("Starting 3-second test recording...")
        output_path = recorder.start_recording()
        print(f"Recording to: {output_path}")
        
        # Record for 3 seconds
        import time
        time.sleep(3)
        
        # Stop recording
        result_path = recorder.stop_recording()
        
        if result_path and result_path.exists():
            size = result_path.stat().st_size
            print(f"✅ Recording successful! File: {result_path} (Size: {size} bytes)")
            return True
        else:
            print("❌ Recording failed - no file created")
            return False
            
    except Exception as e:
        print(f"❌ Recording error: {e}")
        return False

if __name__ == "__main__":
    print("ScribeVault Audio Test")
    print("=" * 30)
    
    # Test audio devices
    devices_ok = test_audio_devices()
    
    if devices_ok:
        # Test recording
        recording_ok = test_recording()
        
        if recording_ok:
            print("\n🎉 Audio system is working correctly!")
        else:
            print("\n⚠️ Audio recording failed")
    else:
        print("\n⚠️ No audio devices found")
        
    print("\nPress Enter to exit...")
    input()
