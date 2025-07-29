"""
AI summarization service for ScribeVault.
"""

import openai
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class SummarizerService:
    """Handles text summarization using OpenAI GPT."""
    
    def __init__(self):
        """Initialize the summarizer service."""
        self.client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
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
