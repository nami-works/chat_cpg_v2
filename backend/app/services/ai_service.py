import asyncio
import json
import logging
import time
import os
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

import openai
import groq
from anthropic import Anthropic
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory

from ..core.config import settings
from ..models.chat import AIModel, MessageRole

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Base exception for AI service errors."""
    pass


class AIProviderError(AIServiceError):
    """Exception for AI provider-specific errors."""
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
        provider: str,
        metadata: Optional[Dict] = None
    ):
        self.content = content
        self.model = model
        self.usage = usage
        self.cost_usd = cost_usd
        self.response_time_ms = response_time_ms
        self.provider = provider
        self.metadata = metadata or {}


class AIService:
    """
    Unified AI service supporting multiple providers:
    - OpenAI (GPT-3.5, GPT-4)
    - Groq (Mixtral, Llama)
    - Anthropic (Claude)
    """
    
    def __init__(self):
        self.openai_client = None
        self.groq_client = None
        self.anthropic_client = None
        
        # Initialize clients
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
            self.openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        if settings.GROQ_API_KEY:
            self.groq_client = groq.Groq(api_key=settings.GROQ_API_KEY)
        
        if hasattr(settings, 'ANTHROPIC_API_KEY') and settings.ANTHROPIC_API_KEY:
            self.anthropic_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        
        # Model pricing (USD per 1K tokens)
        self.pricing = {
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
            "mixtral-8x7b-32768": {"input": 0.0007, "output": 0.0007},
            "llama2-70b-4096": {"input": 0.0007, "output": 0.0008},
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
            "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
        }
        
        # Load references and guidelines
        self.references = self._load_references()
        self.guidelines = self._load_guidelines()
        
        self.models = {
            'openai': {
                'gpt-4o-mini': 'gpt-4o-mini',
                'gpt-4o': 'gpt-4o',
                'gpt-3.5-turbo': 'gpt-3.5-turbo',
                'gpt-3.5-turbo-16k': 'gpt-3.5-turbo-16k',
                'gpt-3.5-turbo-instruct': 'gpt-3.5-turbo-instruct',
            },
            'groq': {
                'llama3-groq-70b': 'llama3-groq-70b-8192-tool-use-preview',
                'llama3-groq-8b': 'llama3-groq-8b-8192-tool-use-preview',
                'llama-3.3-70b': 'llama-3.3-70b-versatile',
                'llama-3.1-8b': 'llama-3.1-8b-instant',
                'compound-beta': 'compound-beta',
            }
        }
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD for token usage."""
        try:
            if model not in self.pricing:
                logger.warning(f"No pricing data for model {model}, using default")
                return 0.0
            
            pricing = self.pricing[model]
            input_cost = (input_tokens / 1000) * pricing["input"]
            output_cost = (output_tokens / 1000) * pricing["output"]
            
            return round(input_cost + output_cost, 6)
        except Exception as e:
            logger.error(f"Error calculating cost: {e}")
            return 0.0
    
    def _get_provider_for_model(self, model: str) -> str:
        """Determine which provider handles the given model."""
        if model.startswith("gpt"):
            return "openai"
        elif model in ["mixtral-8x7b-32768", "llama2-70b-4096"]:
            return "groq"
        elif model.startswith("claude"):
            return "anthropic"
        else:
            raise AIServiceError(f"Unsupported model: {model}")
    
    def _prepare_messages_for_provider(
        self, 
        messages: List[ChatMessage], 
        provider: str
    ) -> List[Dict]:
        """Convert messages to provider-specific format."""
        if provider == "anthropic":
            # Claude has different message format requirements
            formatted_messages = []
            for msg in messages:
                if msg.role == "system":
                    # Claude handles system messages differently
                    continue
                formatted_messages.append(msg.to_dict())
            return formatted_messages
        else:
            # OpenAI and Groq use similar formats
            return [msg.to_dict() for msg in messages]
    
    def _extract_system_prompt(self, messages: List[ChatMessage]) -> Tuple[str, List[ChatMessage]]:
        """Extract system prompt and return remaining messages."""
        system_prompt = ""
        filtered_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_prompt += msg.content + "\n"
            else:
                filtered_messages.append(msg)
        
        return system_prompt.strip(), filtered_messages
    
    async def _call_openai(
        self,
        model: str,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AIResponse:
        """Call OpenAI API."""
        if not self.openai_client:
            raise AIProviderError("OpenAI client not initialized")
        
        try:
            start_time = time.time()
            
            formatted_messages = self._prepare_messages_for_provider(messages, "openai")
            
            response = await self.openai_client.chat.completions.create(
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
                provider="openai",
                metadata={"finish_reason": response.choices[0].finish_reason}
            )
            
        except openai.RateLimitError as e:
            raise AIRateLimitError(f"OpenAI rate limit: {str(e)}")
        except openai.APIError as e:
            raise AIProviderError(f"OpenAI API error: {str(e)}")
        except Exception as e:
            raise AIServiceError(f"OpenAI unexpected error: {str(e)}")
    
    async def _call_groq(
        self,
        model: str,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AIResponse:
        """Call Groq API."""
        if not self.groq_client:
            raise AIProviderError("Groq client not initialized")
        
        try:
            start_time = time.time()
            
            formatted_messages = self._prepare_messages_for_provider(messages, "groq")
            
            # Groq is synchronous, so we run it in a thread pool
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.groq_client.chat.completions.create(
                    model=model,
                    messages=formatted_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
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
                provider="groq",
                metadata={"finish_reason": response.choices[0].finish_reason}
            )
            
        except Exception as e:
            if "rate_limit" in str(e).lower():
                raise AIRateLimitError(f"Groq rate limit: {str(e)}")
            raise AIProviderError(f"Groq API error: {str(e)}")
    
    async def _call_anthropic(
        self,
        model: str,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AIResponse:
        """Call Anthropic API."""
        if not self.anthropic_client:
            raise AIProviderError("Anthropic client not initialized")
        
        try:
            start_time = time.time()
            
            # Extract system prompt for Claude
            system_prompt, filtered_messages = self._extract_system_prompt(messages)
            formatted_messages = self._prepare_messages_for_provider(filtered_messages, "anthropic")
            
            # Anthropic is synchronous, so we run it in a thread pool
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.anthropic_client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_prompt if system_prompt else None,
                    messages=formatted_messages,
                    **kwargs
                )
            )
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Extract response data
            content = response.content[0].text
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
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
                provider="anthropic",
                metadata={"stop_reason": response.stop_reason}
            )
            
        except Exception as e:
            if "rate_limit" in str(e).lower():
                raise AIRateLimitError(f"Anthropic rate limit: {str(e)}")
            raise AIProviderError(f"Anthropic API error: {str(e)}")
    
    async def generate_response(
        self,
        model: str,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AIResponse:
        """
        Generate AI response using the appropriate provider.
        
        Args:
            model: AI model to use
            messages: List of chat messages
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
        
        Returns:
            AIResponse with generated content and metadata
        """
        try:
            provider = self._get_provider_for_model(model)
            
            logger.info(f"Generating response with {provider} model {model}")
            
            if provider == "openai":
                return await self._call_openai(model, messages, temperature, max_tokens, **kwargs)
            elif provider == "groq":
                return await self._call_groq(model, messages, temperature, max_tokens, **kwargs)
            elif provider == "anthropic":
                return await self._call_anthropic(model, messages, temperature, max_tokens, **kwargs)
            else:
                raise AIServiceError(f"Unsupported provider: {provider}")
        
        except (AIServiceError, AIProviderError, AIRateLimitError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error in generate_response: {e}")
            raise AIServiceError(f"Unexpected error: {str(e)}")
    
    async def generate_title(
        self, 
        conversation_messages: List[ChatMessage], 
        model: str = "gpt-3.5-turbo"
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
    
    def get_available_models(self) -> Dict[str, Dict[str, str]]:
        """Get all available models"""
        return self.models
    
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        provider = self._get_provider_for_model(model)
        pricing = self.pricing.get(model, {"input": 0, "output": 0})
        
        return {
            "model": model,
            "provider": provider,
            "pricing": pricing,
            "context_window": self._get_context_window(model),
            "supports_streaming": provider in ["openai", "anthropic"]
        }
    
    def _get_context_window(self, model: str) -> int:
        """Get context window size for model."""
        context_windows = {
            "gpt-3.5-turbo": 16385,
            "gpt-4": 8192,
            "gpt-4-turbo-preview": 128000,
            "mixtral-8x7b-32768": 32768,
            "llama2-70b-4096": 4096,
            "claude-3-haiku-20240307": 200000,
            "claude-3-sonnet-20240229": 200000,
        }
        return context_windows.get(model, 4096)
    
    def _load_references(self) -> Dict[str, str]:
        """Load reference materials"""
        return {
            'ryb': 'Ramping your Brand - comprehensive guide for premium consumer brands',
            'tgcw': 'The Great CEO Within - leadership and business scaling strategies'
        }
    
    def _load_guidelines(self) -> Dict[str, str]:
        """Load guidelines for different functions"""
        return {
            'redacao': self._get_redacao_guidelines(),
            'oraculo': self._get_oraculo_guidelines()
        }
    
    def _get_redacao_guidelines(self) -> str:
        """Guidelines for content creation (redacao)"""
        return """
# Guidelines for LLM model **redacao**

You are a specialist in creative content for premium consumer brands. Your role is to strategically support the brand with high-quality productions that are aligned with its positioning and optimized for impact.

You perform a variety of tasks related to content creation, such as:
- Defining and detailing creative briefs
- Writing blog posts, social media content, and email campaigns
- Creating product descriptions and campaign materials
- Translating style guidelines and benchmarks into original content
- Suggesting titles, headings, and textual structure based on strategic goals
- Adapting tone of voice for different formats and channels

## Task type examples

### 1. Blog Posts Production
→ When receiving a prompt about blog content, apply the blog production logic:

You are an oracle for generating blog post themes.

You should not generate complete blog texts. Your responsibility is to suggest, refine, and validate **short specific themes** (maximum 150 characters each).

In a first interaction, generate between 5 and 10 themes, but if the user asks for more or less, you can accommodate this change.

Then, for each validated specific theme, if the themes are too specific or too focused on the brand's products, making it difficult to effectively obtain semantic field words, you should **automatically generate a corresponding generic version**, composing a second dictionary called `seo_themes`. If the themes don't generate this need, `seo_themes` should be equal to `themes`

### Interaction Rules

#### 1. Basic flow
- Greet the user in a light way.
- Understand the general ideas they want to explore.
- Make provocations and interact with the user **at least 3 times** before defining the final list.
- Refine each idea by suggesting variations and deepening.
- Ensure that final themes have a maximum of 150 characters each.

#### 2. Adaptation to User Style
- Carefully observe the **language, formality, and rhythm** in the user's responses.
- **Mirror** the communication:
  - If the user is **direct and objective**, respond in a **short and practical** way.
  - If the user is **polite, detailed, or formal**, use **complete sentences and respectful tone**.

#### 3. Final Output Format
When ready to provide the final themes, format them as Python dictionaries:

```python
themes = {
    "1. Short summary": "Complete theme title (max 150 chars)",
    "2. Short summary": "Complete theme title (max 150 chars)"
}

seo_themes = {
    "1. Generic keyword": "SEO-optimized version",
    "2. Generic keyword": "SEO-optimized version"
}

macro_name = "descriptive_name_for_theme_set"
```

**Important:** Always provide themes, seo_themes, and macro_name in exactly this format.
"""
    
    def _get_oraculo_guidelines(self) -> str:
        """Guidelines for oracle/consultation mode"""
        return """
# Guidelines for LLM model **oraculo**

You are a strategic business oracle specialized in premium consumer brands. Your role is to provide deep insights, strategic guidance, and expert consultation based on industry best practices and proven frameworks.

You provide strategic consultation on:
- Brand positioning and differentiation
- Market expansion strategies
- Customer segmentation and targeting
- Product development guidance
- Marketing strategy optimization
- Business growth planning
- Competitive analysis
- Customer experience design

You rely on proven business frameworks, industry benchmarks, and strategic thinking methodologies to provide actionable insights.

Always provide specific, actionable recommendations backed by strategic reasoning.
"""
    
    def create_chat_chain(
        self,
        provider: str,
        model: str,
        function_type: str = "general",
        brand_context: Optional[Dict[str, Any]] = None,
        reference: str = "ryb",
        api_key: Optional[str] = None
    ):
        """Create a chat chain with appropriate context and guidelines"""
        
        # Use provided API key or fallback to settings
        actual_api_key = api_key or (settings.OPENAI_API_KEY if provider == 'openai' else settings.GROQ_API_KEY)
        
        if not actual_api_key:
            raise ValueError(f"No API key available for provider: {provider}")
        
        # Get model name
        model_name = self.models.get(provider, {}).get(model)
        if not model_name:
            raise ValueError(f"Unknown model: {provider}/{model}")
        
        # Create the LLM instance
        if provider == 'openai':
            llm = ChatOpenAI(model=model_name, api_key=actual_api_key)
        elif provider == 'groq':
            llm = ChatGroq(model=model_name, api_key=actual_api_key)
        else:
            raise ValueError(f"Unknown provider: {provider}")
        
        # Build context prompt
        context_prompt = self._build_context_prompt(function_type, brand_context, reference)
        
        # Create prompt template
        template = ChatPromptTemplate.from_messages([
            ('system', context_prompt),
            ('placeholder', '{chat_history}'),
            ('user', '{input}')
        ])
        
        # Create chain
        chain = template | llm
        
        return chain
    
    def _build_context_prompt(
        self,
        function_type: str,
        brand_context: Optional[Dict[str, Any]] = None,
        reference: str = "ryb"
    ) -> str:
        """Build the system context prompt"""
        
        # Base context
        context_parts = []
        
        # Add brand context if available
        if brand_context:
            context_parts.append("You have several information about the user's business:")
            
            if brand_context.get('brand_description'):
                context_parts.append(f"- Brand: {brand_context['brand_description']}")
            
            if brand_context.get('products_info'):
                context_parts.append(f"- Products: {brand_context['products_info']}")
            
            if brand_context.get('style_guide'):
                context_parts.append(f"- Style Guide: {brand_context['style_guide']}")
            
            if brand_context.get('blog_url'):
                context_parts.append(f"- Blog: {brand_context['blog_url']}")
            
            if brand_context.get('benchmarks'):
                benchmarks_str = ", ".join(brand_context['benchmarks'])
                context_parts.append(f"- Benchmarks: {benchmarks_str}")
            
            context_parts.append("")
        
        # Add function-specific guidelines
        if function_type in self.guidelines:
            context_parts.append("Besides that, you've been given detailed guidelines for this specific interaction:")
            context_parts.append(self.guidelines[function_type])
            context_parts.append("")
        
        # Add reference
        reference_text = self.references.get(reference, "industry best practices")
        context_parts.append(f"Use {reference_text} as your main reference of knowledge and best practices.")
        context_parts.append("")
        
        context_parts.append("Use all of that as the main ground for all your interactions.")
        
        return "\n".join(context_parts)
    
    async def generate_response(
        self,
        chain,
        message: str,
        memory: ConversationBufferMemory,
        function_type: str = "general"
    ) -> str:
        """Generate AI response using the chain"""
        
        try:
            # Get conversation history
            chat_history = memory.chat_memory.messages
            
            # Invoke the chain
            response = await chain.ainvoke({
                'input': message,
                'chat_history': chat_history
            })
            
            # Extract content from response
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            # Save to memory
            memory.chat_memory.add_user_message(message)
            memory.chat_memory.add_ai_message(response_text)
            
            return response_text
            
        except Exception as e:
            raise Exception(f"Error generating AI response: {str(e)}")
    
    def parse_creative_outputs(self, response_text: str) -> Dict[str, Any]:
        """Parse themes, seo_themes, and macro_name from AI response"""
        result = {}
        
        # Parse themes dictionary
        theme_pattern = re.search(r'themes\s*=\s*\{[^}]+\}', response_text, re.DOTALL)
        if theme_pattern:
            try:
                theme_text = theme_pattern.group(0)
                # Simple parsing for dictionary content
                theme_content = theme_text.split('=')[1].strip()
                if theme_content.startswith('{') and theme_content.endswith('}'):
                    # Extract key-value pairs
                    content = theme_content[1:-1]  # Remove braces
                    pairs = re.findall(r'"([^"]+)":\s*"([^"]+)"', content)
                    if pairs:
                        result['themes'] = dict(pairs)
            except Exception:
                pass
        
        # Parse seo_themes dictionary
        seo_theme_pattern = re.search(r'seo_themes\s*=\s*\{[^}]+\}', response_text, re.DOTALL)
        if seo_theme_pattern:
            try:
                seo_theme_text = seo_theme_pattern.group(0)
                seo_theme_content = seo_theme_text.split('=')[1].strip()
                if seo_theme_content.startswith('{') and seo_theme_content.endswith('}'):
                    content = seo_theme_content[1:-1]
                    pairs = re.findall(r'"([^"]+)":\s*"([^"]+)"', content)
                    if pairs:
                        result['seo_themes'] = dict(pairs)
            except Exception:
                pass
        
        # Parse macro_name
        macro_name_pattern = re.search(r'macro_name\s*=\s*["\']([^"\']+)["\']', response_text)
        if macro_name_pattern:
            try:
                result['macro_name'] = macro_name_pattern.group(1)
            except Exception:
                pass
        
        return result
    
    def get_available_functions(self) -> List[str]:
        """Get available function types"""
        return ['redacao', 'oraculo', 'general']
    
    def get_available_references(self) -> Dict[str, str]:
        """Get available reference materials."""
        return self.references

    # MVP: Simple response method for basic chat functionality
    async def generate_simple_response(
        self,
        user_message: str,
        brand_context: str = "",
        model_provider: str = "openai",
        model_name: str = "gpt-4o-mini",
        api_key: Optional[str] = None
    ) -> str:
        """
        Generate a simple AI response for MVP functionality.
        This is a simplified version without complex chains or memory.
        """
        try:
            # Build basic system prompt
            system_prompt = "You are a helpful AI assistant for beauty and cosmetics brands."
            
            if brand_context:
                system_prompt += f"\n\nBrand Context:\n{brand_context}"
                system_prompt += "\n\nPlease provide helpful advice and information related to this brand when relevant."
            
            # Create messages
            messages = [
                ChatMessage("system", system_prompt),
                ChatMessage("user", user_message)
            ]
            
            # Generate response using the main generate_response method
            response = await self.generate_response(
                model=model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating simple response: {e}")
            return f"I apologize, but I encountered an error while processing your request. Please try again later." 