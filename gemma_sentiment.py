"""gemma_sentiment.py - Gemma 4 Financial Sentiment Analyzer for StockSight
Leverages Google's Gemma 4 open models (gemma-4-26b-a4b-it / gemma-4-31b-it)
via Google GenAI SDK to perform deep financial sentiment analysis, multi-step reasoning,
and financial catalyst identification.

Compatible with Python 3.10+ and integrates seamlessly into StockSight.
"""

import os
import json
import logging
from typing import Dict, Any, Tuple, Optional, List

logger = logging.getLogger(__name__)

# Supported models
DEFAULT_GEMMA_MODEL = "gemma-4-26b-a4b-it"
SUPPORTED_GEMMA_MODELS = ["gemma-4-26b-a4b-it", "gemma-4-31b-it"]


def _get_default_api_key() -> Optional[str]:
    """Retrieve API key from env or config file."""
    if os.getenv("GEMINI_API_KEY"):
        return os.getenv("GEMINI_API_KEY")
    try:
        import config
        if hasattr(config, "gemma_api_key") and config.gemma_api_key:
            return config.gemma_api_key
    except Exception:
        pass
    return None


class GemmaSentimentAnalyzer:
    """Financial sentiment analyzer powered by Google Gemma 4 models."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_GEMMA_MODEL,
        thinking: bool = True
    ):
        self.api_key = api_key or _get_default_api_key()
        self.model = model
        self.thinking = thinking
        self.client = None

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info("Initialized GemmaSentimentAnalyzer with model: %s", self.model)
            except Exception as e:
                logger.warning("Could not initialize GenAI client: %s", e)
        else:
            logger.warning("No Gemini/Gemma API key found. Gemma sentiment will run in fallback mode.")

    def analyze(self, text: str, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Analyze text for financial sentiment using Gemma 4.

        Returns a dictionary containing:
            - polarity: float (-1.0 to 1.0)
            - subjectivity: float (0.0 to 1.0)
            - sentiment: 'positive', 'negative', or 'neutral'
            - confidence: float (0.0 to 1.0)
            - reasoning: explanation of why this text impacts the stock
            - key_catalysts: key market factors identified
        """
        if not self.client:
            return self._fallback_analyze(text)

        from google.genai import types

        context_symbol = f" regarding stock ticker {symbol}" if symbol else ""
        prompt = f"""You are an elite quantitative financial analyst and sentiment expert.
Analyze the following text{context_symbol} and determine its likely financial market impact and sentiment.

Text:
\"\"\"{text}\"\"\"

Provide your response in strictly valid JSON format with the following keys:
{{
    "sentiment": "positive" | "negative" | "neutral",
    "polarity": <float between -1.0 (extremely bearish/negative) and 1.0 (extremely bullish/positive)>,
    "subjectivity": <float between 0.0 (strictly factual) and 1.0 (pure opinion/speculation)>,
    "confidence": <float between 0.0 and 1.0>,
    "reasoning": "<concise 1-2 sentence explanation of the financial rationale>",
    "key_catalysts": ["<catalyst 1>", "<catalyst 2>"]
}}
"""

        try:
            config_args = {
                "response_mime_type": "application/json"
            }
            if self.thinking:
                config_args["thinking_config"] = types.ThinkingConfig(thinking_level="high")

            config = types.GenerateContentConfig(**config_args)

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config
            )

            raw_text = response.text.strip()
            # Clean possible markdown formatting
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

            result = json.loads(raw_text)
            # Ensure standard output
            result["sentiment"] = str(result.get("sentiment", "neutral")).lower()
            if result["sentiment"] not in ["positive", "negative", "neutral"]:
                pol = float(result.get("polarity", 0.0))
                result["sentiment"] = "positive" if pol > 0.05 else ("negative" if pol < -0.05 else "neutral")

            result["polarity"] = float(result.get("polarity", 0.0))
            result["subjectivity"] = float(result.get("subjectivity", 0.5))
            result["confidence"] = float(result.get("confidence", 0.8))
            if "key_catalysts" not in result:
                result["key_catalysts"] = []
            return result

        except Exception as e:
            logger.error("Gemma 4 sentiment analysis error: %s", e)
            return self._fallback_analyze(text)

    def _fallback_analyze(self, text: str) -> Dict[str, Any]:
        """Fallback to basic heuristic analysis if API call fails."""
        return {
            "sentiment": "neutral",
            "polarity": 0.0,
            "subjectivity": 0.5,
            "confidence": 0.0,
            "reasoning": "Fallback analysis (Gemma API unavailable)",
            "key_catalysts": []
        }

    def sentiment_tuple(self, text: str, symbol: Optional[str] = None) -> Tuple[float, float, str]:
        """Returns (polarity, subjectivity, sentiment) matching StockSight's original return format."""
        res = self.analyze(text, symbol)
        return res["polarity"], res["subjectivity"], res["sentiment"]

    def ask(self, question: str, symbol: Optional[str] = None) -> str:
        """Interactive Q&A using Gemma 4 for market intelligence."""
        if not self.client:
            return "Gemma API client not initialized. Please set GEMINI_API_KEY."

        context = f"For stock symbol {symbol}: " if symbol else ""
        prompt = f"You are a financial market expert. {context}{question}"
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"Error querying Gemma 4: {e}"
