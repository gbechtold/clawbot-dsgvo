"""Content analysis module using Ollama LLM."""
import logging
import json
import httpx

from config import settings
from models.schemas import AnalysisResult

logger = logging.getLogger(__name__)


async def analyze_content(anonymized_content: str) -> AnalysisResult:
    """
    Analyze anonymized content using Ollama LLM.

    The LLM processes only anonymized content, ensuring no PII reaches the model.

    Args:
        anonymized_content: Content with PII replaced by pseudonyms

    Returns:
        AnalysisResult with category, urgency, sentiment, and summary
    """
    prompt = f"""Analyze this customer feedback and provide:
1. Category (complaint, request, question, praise, suggestion)
2. Urgency (low, medium, high, critical)
3. Sentiment (positive, neutral, negative)
4. Brief summary (max 50 words)

Feedback:
{anonymized_content}

Respond ONLY with valid JSON in this exact format:
{{
  "category": "complaint",
  "urgency": "medium",
  "sentiment": "negative",
  "summary": "Brief summary here"
}}"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.ollama_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9
                    }
                }
            )

            if response.status_code != 200:
                logger.error(f"Ollama request failed: {response.status_code} - {response.text}")
                return _fallback_analysis(anonymized_content)

            result = response.json()
            response_text = result.get("response", "")

            # Extract JSON from response
            try:
                # Try to find JSON in the response
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1

                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    analysis_data = json.loads(json_str)

                    return AnalysisResult(
                        category=analysis_data.get("category", "unknown"),
                        urgency=analysis_data.get("urgency", "medium"),
                        sentiment=analysis_data.get("sentiment", "neutral"),
                        summary=analysis_data.get("summary", "No summary available")
                    )
                else:
                    logger.warning("No JSON found in LLM response, using fallback")
                    return _fallback_analysis(anonymized_content)

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.debug(f"Raw response: {response_text}")
                return _fallback_analysis(anonymized_content)

    except httpx.TimeoutException:
        logger.error("Ollama request timed out")
        return _fallback_analysis(anonymized_content)
    except Exception as e:
        logger.error(f"LLM analysis failed: {e}", exc_info=True)
        return _fallback_analysis(anonymized_content)


def _fallback_analysis(content: str) -> AnalysisResult:
    """
    Provide a basic fallback analysis when LLM is unavailable.

    Args:
        content: Content to analyze

    Returns:
        Basic AnalysisResult
    """
    # Simple keyword-based fallback
    content_lower = content.lower()

    # Determine sentiment
    positive_words = ["thank", "great", "excellent", "happy", "love", "perfect"]
    negative_words = ["bad", "terrible", "worst", "hate", "problem", "issue", "broken"]

    positive_count = sum(1 for word in positive_words if word in content_lower)
    negative_count = sum(1 for word in negative_words if word in content_lower)

    if positive_count > negative_count:
        sentiment = "positive"
    elif negative_count > positive_count:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    # Determine category
    if any(word in content_lower for word in ["complaint", "problem", "issue", "broken", "not working"]):
        category = "complaint"
    elif any(word in content_lower for word in ["request", "need", "want", "could you"]):
        category = "request"
    elif any(word in content_lower for word in ["question", "how", "what", "when", "where", "why"]):
        category = "question"
    elif any(word in content_lower for word in ["thank", "great", "excellent", "love"]):
        category = "praise"
    else:
        category = "suggestion"

    # Determine urgency
    if any(word in content_lower for word in ["urgent", "asap", "immediately", "critical", "emergency"]):
        urgency = "critical"
    elif any(word in content_lower for word in ["soon", "important", "quickly"]):
        urgency = "high"
    else:
        urgency = "medium"

    return AnalysisResult(
        category=category,
        urgency=urgency,
        sentiment=sentiment,
        summary=content[:100] + "..." if len(content) > 100 else content
    )
