"""Content analysis module using Ollama LLM – liefert numerisches Sentiment."""
import logging
import json
import httpx

from config import settings
from models.schemas import AnalysisResult

logger = logging.getLogger(__name__)

# Sentiment-Mapping: Wort → Float
SENTIMENT_MAP = {
    "very_positive": 0.9, "sehr_positiv": 0.9,
    "positive": 0.6,      "positiv": 0.6,
    "neutral": 0.0,
    "negative": -0.6,     "negativ": -0.6,
    "very_negative": -0.9, "sehr_negativ": -0.9,
}

# Urgency-Mapping: Wort → Wert (für Normalisierung)
URGENCY_MAP = {"low": 1, "medium": 2, "high": 3, "critical": 4}


def _sentiment_to_float(value) -> float:
    """Konvertiert Sentiment-String oder Zahl zu Float -1.0..+1.0."""
    if isinstance(value, (int, float)):
        v = float(value)
        return max(-1.0, min(1.0, v))
    s = str(value).lower().strip()
    if s in SENTIMENT_MAP:
        return SENTIMENT_MAP[s]
    try:
        return max(-1.0, min(1.0, float(s)))
    except ValueError:
        return 0.0


async def analyze_content(anonymized_content: str) -> AnalysisResult:
    """
    Analysiert anonymisierten Text via Ollama.

    Gibt Kategorie, Dringlichkeit und numerisches Sentiment (-1..+1) zurück.
    Kein PII verlässt das System – nur anonymisierter Text wird ans LLM gesendet.

    Args:
        anonymized_content: Text mit ersetzten PII-Feldern

    Returns:
        AnalysisResult mit category, urgency, sentiment (float), summary
    """
    prompt = f"""Analysiere dieses Kunden-Feedback auf Deutsch und antworte NUR mit validem JSON.

Feedback:
{anonymized_content}

Antworte AUSSCHLIESSLICH mit diesem JSON-Format (keine weiteren Texte):
{{
  "category": "complaint|request|question|praise|suggestion",
  "urgency": "low|medium|high|critical",
  "sentiment": <Zahl zwischen -1.0 (sehr negativ) und +1.0 (sehr positiv)>,
  "summary": "<Zusammenfassung in max. 40 Wörtern auf Deutsch>"
}}

Hinweise:
- complaint = Beschwerde/Problem
- request = Wunsch/Anfrage
- question = Frage/Nachfrage  
- praise = Lob/positives Feedback
- critical = sofortiger Handlungsbedarf (Hygiene, Gesundheit, Lebensmittelsicherheit, Verletzung, Unfall, Vergiftung, Notfall)
- Sentiment: -1.0 = sehr wütend, 0.0 = neutral, +1.0 = sehr begeistert"""

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
                f"{settings.ollama_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.05, "top_p": 0.9},
                }
            )

            if response.status_code != 200:
                logger.error(f"Ollama Fehler: {response.status_code}")
                return _fallback_analysis(anonymized_content)

            raw = response.json().get("response", "")
            logger.debug(f"LLM raw response: {raw[:200]}")

            # JSON aus Antwort extrahieren
            j_start = raw.find("{")
            j_end = raw.rfind("}") + 1
            if j_start >= 0 and j_end > j_start:
                data = json.loads(raw[j_start:j_end])
                return AnalysisResult(
                    category=data.get("category", "unknown"),
                    urgency=data.get("urgency", "medium"),
                    sentiment=_sentiment_to_float(data.get("sentiment", 0)),
                    summary=data.get("summary", ""),
                )
            else:
                logger.warning("Kein JSON in LLM-Antwort – Fallback")
                return _fallback_analysis(anonymized_content)

    except httpx.TimeoutException:
        logger.error("Ollama Timeout")
        return _fallback_analysis(anonymized_content)
    except Exception as e:
        logger.error(f"LLM-Analyse fehlgeschlagen: {e}", exc_info=True)
        return _fallback_analysis(anonymized_content)


def _fallback_analysis(content: str) -> AnalysisResult:
    """Keyword-basierter Fallback wenn Ollama nicht erreichbar."""
    c = content.lower()

    # Sentiment
    pos = sum(1 for w in ["super","toll","top","danke","freundlich","wunderbar","prima","perfekt","klasse"] if w in c)
    neg = sum(1 for w in ["problem","beschwerde","schlecht","nicht","fehler","hygiene","skandal","sofort","gravierend","nie wieder"] if w in c)
    sentiment = round(min(1.0, pos * 0.3) - min(1.0, neg * 0.3), 2)

    # Kategorie
    if any(w in c for w in ["beschwerde","problem","nicht geliefert","zu viel verrechnet","hygiene","fehler"]):
        category = "complaint"
    elif any(w in c for w in ["führt ihr","gibt es","wo finde","online bestell","wann"]):
        category = "question"
    elif any(w in c for w in ["bitte liefern","würde gern","wünsche"]):
        category = "request"
    elif any(w in c for w in ["super","toll","danke","freundlich","top","prima"]):
        category = "praise"
    else:
        category = "suggestion"

    # Urgency – Issue #2: extended critical keyword list for safety/hygiene
    if any(w in c for w in [
        "hygiene","gesundheit","lebensmittel","vergiftung","verletzung","unfall",
        "gefährlich","sofortiger","dringend","notfall","rohes fleisch","handschuhe",
        "sofort","kritisch","skandal",
    ]):
        urgency = "critical"
    elif any(w in c for w in ["schnell","bald","wichtig","unverzüglich"]):
        urgency = "high"
    elif any(w in c for w in ["wenn möglich","gelegentlich"]):
        urgency = "low"
    else:
        urgency = "medium"

    return AnalysisResult(
        category=category,
        urgency=urgency,
        sentiment=sentiment,
        summary=content[:120] + "…" if len(content) > 120 else content,
    )
