#!/usr/bin/env python3
"""
Test script for ScribeVault configuration system.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.settings import SettingsManager, CostEstimator
from transcription.whisper_service import check_local_whisper_availability

def test_configuration():
    """Test the configuration system."""
    print("🧪 Testing ScribeVault Configuration System")
    print("=" * 50)
    
    # Test settings manager
    print("\n1. Testing SettingsManager...")
    settings_manager = SettingsManager()
    print(f"   ✅ Settings loaded successfully")
    print(f"   📍 Config path: {settings_manager.config_file}")
    print(f"   🔧 Service: {settings_manager.settings.transcription.service}")
    print(f"   🌍 Language: {settings_manager.settings.transcription.language}")
    
    # Test cost estimation
    print("\n2. Testing Cost Estimation...")
    estimator = CostEstimator()
    
    # Test with 5 minutes of audio
    test_minutes = 5
    openai_cost = estimator.estimate_openai_cost(test_minutes)
    local_cost = estimator.estimate_local_cost(test_minutes)
    
    print(f"   💰 OpenAI cost for {test_minutes}min: ${openai_cost['total']:.4f}")
    print(f"   💰 Local cost for {test_minutes}min: ${local_cost['total']:.4f}")
    savings = openai_cost['total'] - local_cost['total']
    savings_percent = (savings / openai_cost['total'] * 100) if openai_cost['total'] > 0 else 0
    print(f"   💡 Savings: ${savings:.4f} ({savings_percent:.1f}%)")
    
    # Test service comparison
    print("\n3. Testing Service Comparison...")
    comparison = CostEstimator.get_service_comparison()
    
    for service_name, service_data in comparison.items():
        print(f"   📊 {service_data['name']}:")
        print(f"      💵 Cost/min: ${service_data['cost_per_minute']:.4f}")
        print(f"      💵 Cost/hour: ${service_data['cost_per_hour']:.2f}")
        print(f"      ⚡ Setup: {service_data['setup_difficulty']}")
        print(f"      🚀 Speed: {service_data['processing_speed']}")
    
    # Test local Whisper availability
    print("\n4. Testing Local Whisper Availability...")
    availability = check_local_whisper_availability()
    
    print(f"   🎯 Available: {'✅ Yes' if availability['available'] else '❌ No'}")
    if availability['available']:
        print(f"   🤖 Models: {', '.join(availability['models'])}")
        device_info = availability.get('device_info', {})
        if device_info:
            print(f"   💻 CPU cores: {device_info.get('cpu_cores', 'Unknown')}")
            if device_info.get('cuda_available'):
                print(f"   🎮 CUDA GPUs: {device_info.get('cuda_count', 0)}")
            else:
                print(f"   🎮 CUDA: Not available")
    else:
        print(f"   ❌ Error: {availability.get('error', 'Unknown error')}")
        print(f"   💡 To install: pip install whisper torch")
    
    # Test settings persistence
    print("\n5. Testing Settings Persistence...")
    original_service = settings_manager.settings.transcription.service
    
    # Change setting
    settings_manager.settings.transcription.service = "local"
    settings_manager.save_settings()
    print(f"   ✅ Changed service to: local")
    
    # Load new instance to verify persistence
    new_settings_manager = SettingsManager()
    loaded_service = new_settings_manager.settings.transcription.service
    print(f"   ✅ Loaded service: {loaded_service}")
    
    # Restore original setting
    settings_manager.settings.transcription.service = original_service
    settings_manager.save_settings()
    print(f"   ✅ Restored service to: {original_service}")
    
    print("\n🎉 Configuration system test completed successfully!")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Set up OpenAI API key: export OPENAI_API_KEY='your-key-here'")
    print("3. Run the application: python main.py")

if __name__ == "__main__":
    test_configuration()
