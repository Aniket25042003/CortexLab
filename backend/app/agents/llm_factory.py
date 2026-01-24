from typing import Any, List, Optional
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

def get_llm(
    model_name: str = "llama-3.3-70b-versatile",
    temperature: float = 0.3, 
    fallback_model_name: str = "gemini-1.5-flash",
    google_api_key: Optional[str] = None
) -> BaseChatModel:
    """
    Get an LLM instance, prioritizing Groq with Gemini as fallback.
    
    Args:
        model_name: Primary Groq model name
        temperature: Model temperature
        fallback_model_name: Fallback Gemini model name
        
    Returns:
        A Chat model instance (either Groq wrapped with fallback, or just Gemini)
    """
    settings = get_settings()
    
    # Configure Gemini (Backup/Primary if Groq missing)
    gemini_llm = ChatGoogleGenerativeAI(
        model=fallback_model_name,
        google_api_key=settings.google_api_key,
        temperature=temperature,
        convert_system_message_to_human=True
    )
    
    # Check for Groq
    if settings.groq_api_key:
        try:
            logger.info(f"Initializing Groq LLM: {model_name}")
            groq_llm = ChatGroq(
                model=model_name,
                api_key=settings.groq_api_key,
                temperature=temperature,
                max_retries=2
            )
            
            # Create fallback chain
            # When Groq fails (e.g. RateLimit), it switches to Gemini
            return groq_llm.with_fallbacks([gemini_llm])
            
        except Exception as e:
            logger.warning(f"Failed to initialize Groq LLM: {e}. Using Gemini.")
            return gemini_llm
            
    logger.info("Groq API key not found. Using Gemini.")
    return gemini_llm
