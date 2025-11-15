"""LLM API client for log analysis."""
import json
import logging
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for unified LLM API."""

    def __init__(self, api_url: str, api_key: str, default_model: str = "claude-sonnet-4.5"):
        """
        Initialize LLM client.

        Args:
            api_url: LLM API endpoint URL
            api_key: API key for authentication
            default_model: Default model to use
        """
        self.api_url = api_url
        self.api_key = api_key
        self.default_model = default_model

    def analyze_logs(
        self,
        logs: str,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Analyze logs using LLM.

        Args:
            logs: Log content to analyze
            prompt: Analysis prompt/instructions
            model: Model to use (overrides default)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            Dictionary containing analysis results with keys:
                - success: bool
                - model: str
                - response: str
                - findings: List[Dict] (if parseable as JSON)
                - error: str (if failed)
        """
        model = model or self.default_model

        # Build the full prompt
        full_prompt = f"""{prompt}

Here are the logs to analyze:

```
{logs}
```

Please provide your analysis in JSON format with the following structure:
{{
    "findings": [
        {{
            "severity": "critical|warning|info",
            "category": "security|performance|error|other",
            "description": "Brief description",
            "details": "Detailed explanation",
            "recommendation": "What to do about it"
        }}
    ],
    "summary": "Overall summary of findings",
    "highest_severity": "critical|warning|info|none"
}}
"""

        try:
            response = self._call_api(
                prompt=full_prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            if not response:
                return {
                    "success": False,
                    "error": "Empty response from LLM API",
                }

            # Try to parse as JSON
            findings = self._parse_findings(response)

            return {
                "success": True,
                "model": model,
                "response": response,
                "findings": findings,
            }

        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def _call_api(
        self,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> Optional[str]:
        """
        Call the LLM API.

        Args:
            prompt: The prompt to send
            model: Model to use
            max_tokens: Maximum tokens
            temperature: Sampling temperature

        Returns:
            API response text or None if failed
        """
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            logger.info(f"Calling LLM API with model: {model}")
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=60,
            )
            response.raise_for_status()

            data = response.json()

            # Extract response text (format may vary by API)
            # Try common response formats
            if "choices" in data and len(data["choices"]) > 0:
                choice = data["choices"][0]
                if "message" in choice:
                    return choice["message"].get("content", "")
                elif "text" in choice:
                    return choice["text"]

            # Fallback: try to find content anywhere
            if "content" in data:
                return data["content"]

            logger.warning(f"Unexpected API response format: {data}")
            return str(data)

        except requests.exceptions.RequestException as e:
            logger.error(f"LLM API request failed: {e}")
            raise

    def _parse_findings(self, response: str) -> Optional[List[Dict[str, Any]]]:
        """
        Parse LLM response to extract findings.

        Args:
            response: LLM response text

        Returns:
            List of finding dictionaries or None if not parseable
        """
        try:
            # Try to find JSON in the response
            # Sometimes LLMs wrap JSON in markdown code blocks
            response = response.strip()

            # Remove markdown code block markers if present
            if response.startswith("```json"):
                response = response[7:]
            elif response.startswith("```"):
                response = response[3:]

            if response.endswith("```"):
                response = response[:-3]

            response = response.strip()

            # Parse JSON
            data = json.loads(response)

            if isinstance(data, dict) and "findings" in data:
                return data["findings"]
            elif isinstance(data, list):
                return data
            else:
                logger.warning(f"Unexpected JSON structure: {data}")
                return None

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            return None


def get_llm_client() -> LLMClient:
    """
    Get LLM client from settings.

    Returns:
        LLMClient instance
    """
    from src.config import get_settings

    settings = get_settings()
    return LLMClient(
        api_url=settings.llm_api_url,
        api_key=settings.llm_api_key,
        default_model=settings.llm_default_model,
    )
