"""
Hyperspell retrieval for AgentMail Support Bot.
Fetches relevant context from Hyperspell vault (docs, FAQs, support tickets).
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_hyperspell_client = None


def get_hyperspell_client():
    """Get or create AsyncHyperspell client."""
    global _hyperspell_client
    if _hyperspell_client is None:
        api_key = os.getenv("HYPERSPELL_API_KEY")
        user_id = os.getenv("HYPERSPELL_USER_ID", "agentmail-support")
        if not api_key:
            return None
        try:
            from hyperspell import AsyncHyperspell
            _hyperspell_client = AsyncHyperspell(api_key=api_key, user_id=user_id)
        except Exception as e:
            logger.warning(f"Failed to init Hyperspell: {e}")
            return None
    return _hyperspell_client


async def get_context_from_hyperspell(query: str, max_results: int = 15) -> Optional[str]:
    """
    Retrieve relevant context from Hyperspell vault.
    Returns formatted context string for Claude, or None if unavailable.
    """
    client = get_hyperspell_client()
    if not client:
        return None

    try:
        response = await client.memories.search(
            query=query,
            sources=["vault"],
            answer=False,
            options={
                "max_results": max_results,
            }
        )
        if not response.documents:
            return None
        parts = []
        for i, doc in enumerate(response.documents[:10], 1):
            title = getattr(doc, "title", None) or getattr(doc, "resource_id", None) or f"Document {i}"
            content = getattr(doc, "llm_summary", None) or getattr(doc, "text", None) or str(doc)
            parts.append(f"### {title}\n{content}")
        return "\n\n".join(parts)
    except Exception as e:
        logger.warning(f"Hyperspell search failed: {e}")
        return None
