import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseLLMBackend(ABC):
    """Base class for LLM backends that can analyze terminal interactions."""
    
    @abstractmethod
    def analyze_interaction(self, timestamp: str, session_id: str, interaction: list[str]) -> str:
        """Analyze a terminal interaction and return insights.
        
        Args:
            timestamp: The timestamp of the interaction
            session_id: The session identifier
            interaction: List of terminal interaction lines
            
        Returns:
            str: Analysis of the terminal interaction
        """
        pass

class OllamaBackend(BaseLLMBackend):
    """Ollama-based LLM backend using llama3.2 model."""
    
    def __init__(self, model: str = "llama3.2", api_url: str = "http://localhost:11434"):
        """Initialize the Ollama backend.
        
        Args:
            model: The model to use (default: llama2)
            api_url: The Ollama API URL (default: http://localhost:11434)
        """
        self.model = model
        self.api_url = api_url.rstrip('/')
        
    def analyze_interaction(self, timestamp: str, session_id: str, interaction: list[str]) -> str:
        """Analyze a terminal interaction using Ollama."""
        # Prepare the interaction text
        interaction_text = '\n'.join(interaction)
        
        # Prepare the prompt for command analysis
        prompt = f"""Analyze the following terminal interaction and in one small paragraph provide insights about the commands used, their purpose, and any potential improvements or security considerations:

Timestamp: {timestamp}
Session: {session_id}

Interaction:
{interaction_text}

Analysis:"""
        
        try:
            # Make request to Ollama API
            response = requests.post(
                f"{self.api_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            
            # Extract the generated response
            result = response.json()
            return result.get('response', 'No analysis available.')
            
        except Exception as e:
            return f"Error analyzing interaction: {str(e)}"