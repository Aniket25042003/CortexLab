"""
LLM Factory

Provides LLM instances.
Primary: Groq (llama-3.1-8b-instant) — fast, free tier.
Fallback: Gemini — only if Groq is unavailable.
"""

from typing import List, Optional
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

# ── Groq model registry ────────────────────────────────────────────────────────
# User requested llama-3.1-8b-instant as the primary model.
GROQ_MODELS = {
    "fast":    "llama-3.1-8b-instant",       # ← primary; user's requested model
    "kimi":    "llama-3.1-8b-instant",
    "gpt_oss": "llama-3.1-8b-instant",
    "qwen":    "llama-3.1-8b-instant",
    "llama":   "llama-3.1-8b-instant",
    "heavy":   "llama-3.3-70b-versatile",    # use for complex summarisation if needed
}

DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"

# ── Gemini fallback chain ─────────────────────────────────────────────────────
# Only used when Groq key is missing / all Groq calls fail.
GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]


def _make_gemini(model: str, temperature: float, api_key: str) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=temperature,
        max_retries=1,   # fail fast — don't tie up the pipeline waiting on quota
        timeout=60.0,
    )


def get_llm(
    model_name: Optional[str] = None,
    temperature: float = 0.3,
    fallback_model_name: str = "gemini-2.0-flash",
    google_api_key: Optional[str] = None,
) -> BaseChatModel:
    """
    Return an LLM with Groq as primary and Gemini as fallback.

    Priority:
      1. Groq llama-3.1-8b-instant  (if GROK_API is set)
      2. Gemini gemini-2.0-flash    (if GOOGLE_API_KEY is set)
      3. Remaining Gemini models    (cascading fallback)
    """
    settings = get_settings()

    groq_key = settings.groq_api_key
    gemini_key = settings.google_api_key or google_api_key or ""

    # Resolve the Groq model name
    groq_model = GROQ_MODELS.get(model_name or "", DEFAULT_GROQ_MODEL)

    # Build Gemini fallback list (skip if no key)
    gemini_llms: List[BaseChatModel] = []
    if gemini_key:
        requested = fallback_model_name or GEMINI_MODELS[0]
        chain_names = [requested] + [m for m in GEMINI_MODELS if m != requested]
        gemini_llms = [_make_gemini(m, temperature, gemini_key) for m in chain_names]
        logger.debug(f"Gemini fallback chain: {chain_names}")

    # ── Primary: Groq ─────────────────────────────────────────────────────────
    if groq_key:
        try:
            logger.info(f"Using Groq: {groq_model}")
            groq_llm = ChatGroq(
                model=groq_model,
                api_key=groq_key,
                temperature=temperature,
                max_retries=2,
                request_timeout=60.0,
            )
            if gemini_llms:
                return groq_llm.with_fallbacks(gemini_llms)
            return groq_llm
        except Exception as e:
            logger.warning(f"Groq init failed ({groq_model}): {e}. Falling back to Gemini.")
    else:
        logger.warning("GROK_API key not set — skipping Groq, using Gemini only.")

    # ── Fallback: Gemini ──────────────────────────────────────────────────────
    if not gemini_llms:
        raise RuntimeError(
            "No AI API keys found. Set GROK_API (Groq) or GOOGLE_API_KEY (Gemini) in backend/.env"
        )

    logger.info(f"Using Gemini as primary: {GEMINI_MODELS[0]}")
    primary, *rest = gemini_llms
    return primary.with_fallbacks(rest) if rest else primary
