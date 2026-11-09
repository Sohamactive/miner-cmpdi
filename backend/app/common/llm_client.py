"""Provider-agnostic LLM client with JSON mode, retry, and extractive fallback."""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any

logger = logging.getLogger(__name__)

MAX_RETRIES = 5
BASE_BACKOFF_SECONDS = 2.0


def _extract_retry_delay(error: Exception) -> float | None:
    error_text = str(error)
    match = re.search(r"retry in\s+([\d.]+)\s*s", error_text, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    return None


def _is_rate_limit_error(error: Exception) -> bool:
    error_text = str(error).lower()
    return "429" in error_text or "resource_exhausted" in error_text or "quota" in error_text


def _is_retryable_error(error: Exception) -> bool:
    error_text = str(error).lower()
    return (
        _is_rate_limit_error(error)
        or "503" in error_text
        or "500 internal" in error_text
        or "unavailable" in error_text
        or "server disconnected" in error_text
        or "remoteprotocolerror" in error_text
        or "remote protocol" in error_text
        or "connection reset" in error_text
    )


def _extract_json_payload(raw_text: str) -> str:
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    if not text:
        raise ValueError("LLM returned an empty response")
    if text[0] in "[{":
        return text
    first_object = text.find("{")
    first_array = text.find("[")
    starts = [index for index in (first_object, first_array) if index != -1]
    if not starts:
        raise ValueError(f"LLM did not return JSON: {text[:200]}")
    start = min(starts)
    end_object = text.rfind("}")
    end_array = text.rfind("]")
    end = max(end_object, end_array)
    if end < start:
        raise ValueError(f"LLM returned malformed JSON: {text[:200]}")
    return text[start : end + 1]


def _gemini_json_call(prompt: str, *, model: str | None = None) -> dict[str, Any]:
    from google import genai
    from google.genai import types

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not configured")

    model_name = model or os.getenv("LLM_MODEL", "gemini-2.5-flash")
    timeout_ms = int(os.getenv("LLM_TIMEOUT_MS", "120000"))
    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=timeout_ms))

    config = types.GenerateContentConfig(response_mime_type="application/json")

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=model_name, contents=prompt, config=config,
            )
            raw_text = response.text or ""
            return json.loads(_extract_json_payload(raw_text))
        except Exception as error:
            last_error = error
            if not _is_retryable_error(error):
                raise
            suggested_delay = _extract_retry_delay(error)
            backoff = suggested_delay if suggested_delay else BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))
            backoff = min(backoff, 60.0)
            if attempt < MAX_RETRIES:
                logger.warning("Retryable LLM error on attempt %d/%d, waiting %.1fs", attempt, MAX_RETRIES, backoff)
                time.sleep(backoff)
    raise last_error  # type: ignore[misc]


def _bedrock_json_call(prompt: str, *, model: str | None = None) -> dict[str, Any]:
    import boto3
    from botocore.config import Config

    region = os.getenv("AWS_REGION", "us-east-1")
    model_id = model or os.getenv("BEDROCK_MODEL", "google.gemma-4-31b")
    timeout = int(os.getenv("LLM_TIMEOUT_MS", "120000")) / 1000

    client = boto3.client(
        "bedrock-runtime",
        region_name=region,
        config=Config(read_timeout=timeout, connect_timeout=10),
    )

    body = {
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4096,
        "temperature": 0.1,
        "top_p": 0.9,
    }

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.invoke_model(modelId=model_id, body=json.dumps(body))
            payload = json.loads(response["body"].read())
            choices = payload.get("choices")
            if isinstance(choices, list) and choices and isinstance(choices[0], dict):
                message = choices[0].get("message", {})
                content = message.get("content", "") if isinstance(message, dict) else ""
            else:
                output = payload.get("output", payload)
                if isinstance(output, dict) and isinstance(output.get("message"), dict):
                    content = output["message"].get("content", "")
                else:
                    content = output.get("content", "") if isinstance(output, dict) else ""
            if isinstance(content, list):
                content = content[0].get("text", "") if content and isinstance(content[0], dict) else ""
            raw_text = str(content)
            return json.loads(_extract_json_payload(raw_text))
        except Exception as error:
            last_error = error
            if not _is_retryable_error(error):
                raise
            suggested_delay = _extract_retry_delay(error)
            backoff = suggested_delay if suggested_delay else BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))
            backoff = min(backoff, 60.0)
            if attempt < MAX_RETRIES:
                logger.warning("Retryable LLM error on attempt %d/%d, waiting %.1fs", attempt, MAX_RETRIES, backoff)
                time.sleep(backoff)
    raise last_error  # type: ignore[misc]


def _bedrock_mantle_json_call(prompt: str, *, model: str | None = None) -> dict[str, Any]:
    from openai import OpenAI

    api_key = os.getenv("MANTLE_API_KEY", "")
    if not api_key or api_key.startswith("replace_with_"):
        raise RuntimeError("MANTLE_API_KEY not configured")

    timeout = int(os.getenv("LLM_TIMEOUT_MS", "120000")) / 1000
    client = OpenAI(
        base_url=os.getenv(
            "MANTLE_BASE_URL",
            "https://bedrock-mantle.us-east-1.api.aws/v1",
        ),
        api_key=api_key,
        default_headers={"OpenAI-Project": os.getenv("MANTLE_PROJECT", "default")},
        timeout=timeout,
    )
    model_name = model or os.getenv("MANTLE_MODEL", "openai.gpt-oss-120b")

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=int(os.getenv("MANTLE_MAX_TOKENS", "4096")),
                temperature=0.1,
            )
            content = response.choices[0].message.content or ""
            return json.loads(_extract_json_payload(content))
        except Exception as error:
            last_error = error
            if not _is_retryable_error(error):
                raise
            suggested_delay = _extract_retry_delay(error)
            backoff = suggested_delay if suggested_delay else BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))
            if attempt < MAX_RETRIES:
                time.sleep(min(backoff, 60.0))
    raise last_error  # type: ignore[misc]


def _call_provider(prompt: str, *, model: str | None = None) -> dict[str, Any]:
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    if provider in {"bedrock_mantle", "mantle"}:
        return _bedrock_mantle_json_call(prompt, model=model)
    if provider == "bedrock":
        return _bedrock_json_call(prompt, model=model)
    return _gemini_json_call(prompt, model=model)


def generate_json(prompt: str, *, model: str | None = None, list_key: str | None = None) -> dict[str, Any]:
    """Call LLM and return parsed JSON. Raises on failure."""
    provider = os.getenv("LLM_PROVIDER", "gemini")
    configured_model = (
        os.getenv("MANTLE_MODEL", "openai.gpt-oss-120b")
        if provider.lower() in {"bedrock_mantle", "mantle"}
        else model or os.getenv("LLM_MODEL", "gemini-2.5-flash")
    )
    logger.info("LLM request -> provider=%s, model=%s, prompt_length=%d", provider, configured_model, len(prompt))

    payload = _call_provider(prompt, model=model)

    if isinstance(payload, list):
        if list_key is None:
            raise ValueError(f"Expected JSON object, received list")
        return {list_key: payload}
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object, received {type(payload).__name__}")
    return payload


def generate_json_or_none(prompt: str, *, model: str | None = None) -> dict[str, Any] | None:
    """Call LLM, return None on any failure (no crash)."""
    try:
        return generate_json(prompt, model=model)
    except Exception:
        logger.exception("LLM call failed (non-fatal)")
        return None
