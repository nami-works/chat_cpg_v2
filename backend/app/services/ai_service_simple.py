import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

import openai
from ..core.config import settings

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Base exception for AI service errors."""
    pass


class AIRateLimitError(AIServiceError):
    """Exception for rate limit errors."""
    pass


class ChatMessage:
    """Standardized chat message format."""
    
    def __init__(self, role: str, content: str, name: Optional[str] = None):
        self.role = role
        self.content = content
        self.name = name
    
    def to_dict(self) -> Dict[str, Any]:
        msg = {"role": self.role, "content": self.content}
        if self.name:
            msg["name"] = self.name
        return msg


class AIResponse:
    """Standardized AI response format."""
    
    def __init__(
        self,
        content: str,
        model: str,
        usage: Dict[str, int],
        cost_usd: float,
        response_time_ms: int,
        metadata: Optional[Dict] = None
    ):
        self.content = content
        self.model = model
        self.usage = usage
        self.cost_usd = cost_usd
        self.response_time_ms = response_time_ms
        self.metadata = metadata or {}


class SimpleAIService:
    """
    Simplified AI service using only OpenAI as requested.
    """
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise AIServiceError("OpenAI API key not configured")
        
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # OpenAI model pricing (USD per 1K tokens)
        self.pricing = {
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        }
        
        # Available models
        self.available_models = [
            "gpt-4o-mini",
            "gpt-4o", 
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo"
        ]
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD for token usage."""
        try:
            if model not in self.pricing:
                logger.warning(f"No pricing data for model {model}, using gpt-4o-mini pricing")
                model = "gpt-4o-mini"
            
            pricing = self.pricing[model]
            input_cost = (input_tokens / 1000) * pricing["input"]
            output_cost = (output_tokens / 1000) * pricing["output"]
            
            return round(input_cost + output_cost, 6)
        except Exception as e:
            logger.error(f"Error calculating cost: {e}")
            return 0.0
    
    async def generate_response(
        self,
        model: str,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AIResponse:
        """
        Generate AI response using OpenAI.
        
        Args:
            model: OpenAI model to use
            messages: List of chat messages
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional OpenAI parameters
        
        Returns:
            AIResponse with generated content and metadata
        """
        try:
            if model not in self.available_models:
                logger.warning(f"Model {model} not in available models, using gpt-4o-mini")
                model = "gpt-4o-mini"
            
            start_time = time.time()
            
            formatted_messages = [msg.to_dict() for msg in messages]
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Extract response data
            content = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            cost_usd = self.calculate_cost(
                model, 
                usage["prompt_tokens"], 
                usage["completion_tokens"]
            )
            
            return AIResponse(
                content=content,
                model=model,
                usage=usage,
                cost_usd=cost_usd,
                response_time_ms=response_time_ms,
                metadata={"finish_reason": response.choices[0].finish_reason}
            )
            
        except openai.RateLimitError as e:
            raise AIRateLimitError(f"OpenAI rate limit: {str(e)}")
        except openai.APIError as e:
            raise AIServiceError(f"OpenAI API error: {str(e)}")
        except Exception as e:
            raise AIServiceError(f"Unexpected error: {str(e)}")
    
    async def generate_title(
        self, 
        conversation_messages: List[ChatMessage], 
        model: str = "gpt-4o-mini"
    ) -> str:
        """Generate a conversation title based on the messages."""
        try:
            # Use first few messages to generate title
            sample_messages = conversation_messages[:3]
            
            title_prompt = ChatMessage(
                role="system",
                content="Generate a concise, descriptive title (max 60 characters) for this conversation. "
                       "Focus on the main topic or question being discussed. Return only the title."
            )
            
            context_message = ChatMessage(
                role="user",
                content=f"Conversation context:\n\n" + 
                       "\n\n".join([f"{msg.role}: {msg.content[:200]}..." for msg in sample_messages])
            )
            
            response = await self.generate_response(
                model=model,
                messages=[title_prompt, context_message],
                temperature=0.3,
                max_tokens=50
            )
            
            title = response.content.strip().strip('"').strip("'")
            return title[:60] if len(title) > 60 else title
            
        except Exception as e:
            logger.error(f"Error generating title: {e}")
            return "New Conversation"
    
    def get_available_models(self) -> List[str]:
        """Get all available models"""
        return self.available_models
    
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        if model not in self.available_models:
            model = "gpt-4o-mini"
            
        pricing = self.pricing.get(model, {"input": 0, "output": 0})
        
        return {
            "model": model,
            "provider": "openai",
            "pricing": pricing,
            "context_window": self._get_context_window(model),
            "supports_streaming": True
        }
    
    def _get_context_window(self, model: str) -> int:
        """Get context window size for model."""
        context_windows = {
            "gpt-4o-mini": 128000,
            "gpt-4o": 128000,
            "gpt-3.5-turbo": 16385,
            "gpt-4": 8192,
            "gpt-4-turbo": 128000,
        }
        return context_windows.get(model, 16385)


# Create a singleton instance
ai_service = SimpleAIService()