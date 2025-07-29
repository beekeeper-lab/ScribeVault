#!/usr/bin/env python3
"""
Simple audio test to diagnose PyAudio issues.
"""

import pyaudio
import sys

def test_pyaudio():
    """Test PyAudio initialization and device detection."""
    print("🔍 Testing PyAudio...")
    
    try:
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        print("✅ PyAudio initialized successfully")
        
        # Get device count
        device_count = p.get_device_count()
        print(f"📱 Found {device_count} audio devices")
        
        # List input devices
        input_devices = []
        for i in range(device_count):
            try:
                device_info = p.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    input_devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxInputChannels'],
                        'sample_rate': device_info['defaultSampleRate']
                    })
                    print(f"  🎤 Input: {device_info['name']} (Index: {i})")
            except Exception as e:
                print(f"  ❌ Error with device {i}: {e}")
        
        # Try to find a working input device
        working_device = None
        for device in input_devices:
            try:
                # Test opening a stream with this device
                test_stream = p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=44100,
                    input=True,
                    input_device_index=device['index'],
                    frames_per_buffer=1024
                )
                test_stream.close()
                working_device = device
                print(f"✅ Working input device: {device['name']}")
                break
            except Exception as e:
                print(f"❌ Device {device['name']} failed: {e}")
        
        p.terminate()
        
        if working_device:
            print(f"\n🎉 Recommended device: {working_device['name']} (Index: {working_device['index']})")
            return working_device['index']
        else:
            print("\n⚠️ No working input devices found")
            return None
            
    except Exception as e:
        print(f"❌ PyAudio initialization failed: {e}")
        return None

if __name__ == "__main__":
    working_device_index = test_pyaudio()
    
    if working_device_index is not None:
        print(f"\nTo use this device, modify the AudioRecorder to use device index {working_device_index}")
    else:
        print("\nConsider installing/configuring audio drivers or using pulseaudio")
    
    print("\nPress Enter to exit...")
    input()
