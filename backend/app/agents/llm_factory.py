from typing import Any, List, Optional
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

# Groq Model Registry
MODELS = {
    "kimi": "moonshotai/kimi-k2-instruct-0905",  # 10k TPM
    "gpt_oss": "openai/gpt-oss-120b",           # 8k TPM
    "qwen": "qwen/qwen3-32b"                    # 6k TPM
}

def get_llm(
    model_name: Optional[str] = None,
    temperature: float = 0.3, 
    fallback_model_name: str = "gemini-1.5-flash",
    google_api_key: Optional[str] = None
) -> BaseChatModel:
    """
    Get an LLM instance, prioritizing Groq with Gemini as fallback.
    
    Args:
        model_name: Key (kimi, gpt_oss, qwen) or full name of the Groq model.
                   Defaults to k2-instruct if None.
        temperature: Model temperature
        fallback_model_name: Fallback Gemini model name
        
    Returns:
        A Chat model instance (either Groq wrapped with fallback, or just Gemini)
    """
    settings = get_settings()
    
    # Resolve model name
    effective_model = model_name or MODELS["kimi"]
    if effective_model in MODELS:
        effective_model = MODELS[effective_model]
        
    # Configure Gemini (Backup/Primary if Groq missing)
    gemini_llm = ChatGoogleGenerativeAI(
        model=fallback_model_name,
        google_api_key=settings.google_api_key or google_api_key,
        temperature=temperature,
        convert_system_message_to_human=True
    )
    
    # Check for Groq
    if settings.groq_api_key:
        try:
            logger.info(f"Initializing Groq LLM: {effective_model}")
            groq_llm = ChatGroq(
                model=effective_model,
                api_key=settings.groq_api_key,
                temperature=temperature,
                max_retries=2
            )
            
            # Create fallback chain
            return groq_llm.with_fallbacks([gemini_llm])
            
        except Exception as e:
            logger.warning(f"Failed to initialize Groq LLM: {e}. Using Gemini.")
            return gemini_llm
            
    logger.info("Groq API key not found. Using Gemini.")
    return gemini_llm
