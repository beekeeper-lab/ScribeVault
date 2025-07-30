#!/usr/bin/env python3
"""
Test the enhanced markdown summary generation system
"""

import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from export.markdown_generator import MarkdownGenerator
    from ai.summarizer import SummarizerService
    print("✅ Successfully imported markdown and summarizer modules")
    
    # Test data
    test_recording = {
        'filename': 'test_meeting.wav',
        'title': 'Team Planning Meeting',
        'category': 'meeting',
        'duration': 1800,  # 30 minutes
        'transcription': 'This is a test meeting transcript. We discussed the new project requirements and assigned tasks to team members.',
        'created_at': '2025-07-30T15:30:00',
    }
    
    # Test markdown generation
    markdown_gen = MarkdownGenerator()
    
    # Add a test summary
    test_recording['summary'] = """## Participants
- John Smith (Project Manager)
- Sarah Johnson (Developer)
- Mike Chen (Designer)

## Project Context / Purpose
Planning meeting for the new customer portal project

## Technologies or Products Discussed
- React.js for frontend
- Node.js for backend
- PostgreSQL database

## Next Steps and Action Items
- Sarah: Set up development environment by Friday
- Mike: Create initial wireframes by Wednesday
- John: Schedule client review meeting

## Key Quotes or Takeaways
"We need to prioritize user experience over fancy features" - John Smith"""
    
    # Generate markdown file
    markdown_path = markdown_gen.save_markdown_file(test_recording)
    print(f"✅ Markdown file created: {markdown_path}")
    
    # Check if file exists and has content
    if markdown_path.exists():
        content = markdown_path.read_text(encoding='utf-8')
        print(f"✅ File size: {len(content)} characters")
        print("✅ File content preview:")
        print("-" * 50)
        print(content[:500] + "..." if len(content) > 500 else content)
        print("-" * 50)
    else:
        print("❌ Markdown file was not created")
        
    print("\n🎉 Markdown generation test completed successfully!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all required modules are available")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
