import json
import sys
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
        
        # System prompt to provide context about terminal command analysis
        system_prompt = """
You are a terminal command analysis expert, who is talking directly to the user as you observe their terminal interactions. Your role is to analyze terminal interactions and provide insights about:
1. The purpose and functionality of commands being used
2. Potential security implications or risks
3. Best practices and possible improvements
4. Command efficiency and alternatives
5. Common pitfalls or mistakes to avoid

Consider the shell environment, command flags, and overall context of the interaction. Focus on providing practical, security-conscious advice while explaining complex concepts clearly."""
        
        # Prepare the prompt for command analysis
        prompt = f"""{system_prompt}

Analyze the following terminal interaction and in one small paragraph provide insights about the commands used, their purpose, and any potential improvements or security considerations:

Timestamp: {timestamp}
Session: {session_id}

Interaction:
{interaction_text}

Analysis:"""
        
        try:
            # Make request to Ollama API with streaming enabled
            response = requests.post(
                f"{self.api_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": True
                },
                stream=True,
                timeout=30  # Add timeout to prevent hanging
            )
            response.raise_for_status()
            
            # Process the streaming response
            full_response = ""
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    try:
                        # Parse the JSON response
                        chunk = json.loads(line)
                        if 'response' in chunk:
                            # Get the response fragment
                            fragment = chunk['response']
                            if fragment.strip():  # Only process non-empty fragments
                                full_response += fragment
                                yield fragment
                        elif 'error' in chunk:
                            error_msg = f"Ollama error: {chunk['error']}"
                            print(error_msg, file=sys.stderr)
                            yield error_msg
                    except json.JSONDecodeError as e:
                        error_msg = f"Error decoding response: {e}"
                        print(error_msg, file=sys.stderr)
                        yield error_msg
            
            # If no response was received, yield an error message
            if not full_response.strip():
                error_msg = "No response received from Ollama. Please check if the service is running and the model is loaded."
                print(error_msg, file=sys.stderr)
                yield error_msg
            
        except requests.exceptions.Timeout:
            error_msg = "Request to Ollama timed out. Please check the service."
            print(error_msg, file=sys.stderr)
            yield error_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"Error connecting to Ollama: {str(e)}"
            print(error_msg, file=sys.stderr)
            yield error_msg
        except Exception as e:
            error_msg = f"Error analyzing interaction: {str(e)}"
            print(error_msg, file=sys.stderr)
            yield error_msg