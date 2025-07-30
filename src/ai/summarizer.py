"""
AI summarization service for ScribeVault.
"""

import openai
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from pathlib import Path

load_dotenv()

# Import the markdown generator
try:
    from export.markdown_generator import MarkdownGenerator, MarkdownException
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

class SummarizerService:
    """Handles text summarization using OpenAI GPT."""
    
    def __init__(self):
        """Initialize the summarizer service."""
        self.client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize markdown generator if available
        if MARKDOWN_AVAILABLE:
            try:
                self.markdown_generator = MarkdownGenerator()
            except Exception as e:
                print(f"Warning: Could not initialize markdown generator: {e}")
                self.markdown_generator = None
        else:
            self.markdown_generator = None
        
    def summarize_text(self, text: str, style: str = "concise") -> Optional[str]:
        """Generate a summary of the provided text.
        
        Args:
            text: The text to summarize
            style: Summary style ("concise", "detailed", "bullet_points")
            
        Returns:
            Generated summary or None if summarization failed
        """
        try:
            # Define system prompts for different styles
            prompts = {
                "concise": "You are a helpful assistant that creates concise summaries of transcripts.",
                "detailed": "You are a helpful assistant that creates detailed summaries with key points and context.",
                "bullet_points": "You are a helpful assistant that creates bullet-point summaries of transcripts."
            }
            
            system_prompt = prompts.get(style, prompts["concise"])
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Summarize the following transcript:\n\n{text}"}
                ],
                temperature=0.5,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Summarization error: {e}")
            return None
            
    def extract_key_points(self, text: str) -> Optional[list]:
        """Extract key points from the text.
        
        Args:
            text: The text to analyze
            
        Returns:
            List of key points or None if extraction failed
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "Extract 3-5 key points from the transcript. Return them as a JSON array of strings."
                    },
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            # Parse the JSON response
            import json
            key_points = json.loads(response.choices[0].message.content)
            return key_points
            
        except Exception as e:
            print(f"Key point extraction error: {e}")
            return None
            
    def categorize_content(self, text: str) -> Optional[str]:
        """Categorize the content type.
        
        Args:
            text: The text to categorize
            
        Returns:
            Content category or None if categorization failed
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "Categorize this transcript into one of these categories: meeting, lecture, interview, note, call, presentation, other. Return only the category name."
                    },
                    {"role": "user", "content": text}
                ],
                temperature=0.1,
                max_tokens=50
            )
            
            return response.choices[0].message.content.strip().lower()
            
        except Exception as e:
            print(f"Categorization error: {e}")
            return "other"
    
    def generate_summary_with_markdown(
        self, 
        recording_data: Dict[str, Any], 
        style: str = "concise",
        template_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate both text summary and markdown file for a recording.
        
        Args:
            recording_data: Dictionary containing recording information
            style: Summary style ("concise", "detailed", "bullet_points")
            template_prompt: Optional custom template prompt
            
        Returns:
            Dictionary with 'summary' text and 'markdown_path' (if generated)
        """
        result = {
            'summary': None,
            'markdown_path': None,
            'error': None
        }
        
        try:
            # Get transcription for summarization
            transcription = recording_data.get('transcription', '')
            
            if not transcription or not transcription.strip():
                result['error'] = "No transcription available for summarization"
                return result
            
            # Generate summary - use structured format for meetings
            category = recording_data.get('category', 'other')
            
            if category in ['meeting', 'call', 'interview']:
                # Use structured template for business/professional recordings
                summary = self.generate_structured_summary(transcription)
            else:
                # Use standard summary for other types
                summary = self.summarize_text(transcription, style)
            if summary:
                result['summary'] = summary
                
                # Update recording data with summary for markdown generation
                recording_data_with_summary = recording_data.copy()
                recording_data_with_summary['summary'] = summary
                
                # Generate markdown file if possible
                if self.markdown_generator:
                    try:
                        markdown_path = self.markdown_generator.save_markdown_file(
                            recording_data_with_summary, 
                            template_prompt
                        )
                        result['markdown_path'] = str(markdown_path)
                    except MarkdownException as e:
                        print(f"Warning: Failed to generate markdown file: {e}")
                        result['error'] = f"Markdown generation failed: {e}"
                else:
                    result['error'] = "Markdown generator not available"
            else:
                result['error'] = "Failed to generate summary"
            
        except Exception as e:
            print(f"Error in generate_summary_with_markdown: {e}")
            result['error'] = str(e)
        
        return result
    
    def generate_structured_summary(self, transcription: str) -> Optional[str]:
        """Generate a structured professional meeting summary using the custom template.
        
        Args:
            transcription: The full transcription text
            
        Returns:
            Structured summary or None if generation failed
        """
        try:
            structured_prompt = """You are an assistant that creates structured, professional meeting summaries from raw conversation transcripts.

I will provide you with a text file containing a meeting conversation.

Your task:
- Extract and organize key information into a clear, professional format
- Use clear headers and bullet points for readability
- Include the following sections if relevant information is available in the transcript:

**Participants**: List people mentioned or speaking
**Company Overview**: For each company/organization mentioned
**Project Context / Purpose**: Main purpose and context of the meeting
**Technologies or Products Discussed**: Technical solutions, tools, or products mentioned  
**Problems, Constraints, or Pain Points**: Challenges and limitations identified
**Proposed Solutions or Engagement Models**: Recommended approaches and solutions
**Next Steps and Action Items**: Specific follow-up tasks and responsibilities
**Key Quotes or Takeaways**: Important statements or insights

- Summarize in a concise, factual, and professional tone
- If a section has no relevant information from the transcript, mark it as "Not discussed" or omit it
- Focus on extracting actual information from the conversation, not making assumptions

Please analyze the following meeting transcript:"""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": structured_prompt},
                    {"role": "user", "content": f"Meeting Transcript:\n\n{transcription}"}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Structured summary generation error: {e}")
            return None
