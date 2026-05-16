"""Chat completions via OpenAI-compatible APIs (OpenAI, Ollama, Groq, custom)."""

from __future__ import annotations

import asyncio
import time

import httpx
from openai import APIConnectionError, OpenAI, RateLimitError

from discord_ai.config import (
    BASE_SYSTEM_PROMPT,
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    LLM_PROVIDER,
    LLM_TIMEOUT_SECONDS,
    MAX_REPLY_CHARS,
)
from discord_ai.i18n.languages import resolve_language
from discord_ai.i18n.ui import ui_for_user
from discord_ai.logging_setup import get_logger
from discord_ai.services.history import history
from discord_ai.services.settings import settings

log = get_logger("ai")

_client: OpenAI | None = None
_model: str = LLM_MODEL
_provider: str = LLM_PROVIDER


def _resolve_client_config() -> tuple[str, str, str]:
    """Return (base_url, api_key, model)."""
    provider = LLM_PROVIDER
    model = LLM_MODEL

    if provider == "openai":
        return (
            LLM_BASE_URL or "https://api.openai.com/v1",
            LLM_API_KEY,
            model,
        )
    if provider == "ollama":
        return (
            LLM_BASE_URL or "http://127.0.0.1:11434/v1",
            LLM_API_KEY or "ollama",
            model,
        )
    if provider == "groq":
        return (
            LLM_BASE_URL or "https://api.groq.com/openai/v1",
            LLM_API_KEY,
            model,
        )
    if provider == "custom":
        if not LLM_BASE_URL:
            raise RuntimeError("LLM_BASE_URL is required when LLM_PROVIDER=custom")
        return (LLM_BASE_URL, LLM_API_KEY or "none", model)

    raise RuntimeError(
        f"Unknown LLM_PROVIDER={provider}. Use: openai, ollama, groq, custom"
    )


def _check_ollama_reachable(base_url: str) -> None:
    root = base_url.removesuffix("/v1").rstrip("/")
    try:
        resp = httpx.get(f"{root}/api/tags", timeout=5.0)
        resp.raise_for_status()
    except Exception as exc:
        log.warning(
            "Ollama not reachable at %s — run: ollama serve && ollama pull %s (%s)",
            root,
            LLM_MODEL,
            exc,
        )


def init_llm() -> None:
    global _client, _model, _provider

    base_url, api_key, model = _resolve_client_config()
    _provider = LLM_PROVIDER
    _model = model

    if _provider == "ollama":
        _check_ollama_reachable(base_url)

    if _provider in ("openai", "groq", "custom") and not api_key:
        raise RuntimeError(f"LLM_API_KEY required for provider={_provider}")

    timeout = httpx.Timeout(
        connect=15.0,
        read=float(LLM_TIMEOUT_SECONDS),
        write=30.0,
        pool=15.0,
    )
    _client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
    log.info("LLM ready (provider=%s, model=%s, base=%s)", _provider, _model, base_url)


def system_prompt_for(user_id: int) -> str:
    prefs = settings.get(user_id)
    lang = resolve_language(prefs.language)
    return f"{BASE_SYSTEM_PROMPT}\n\n{lang.prompt}"


def _friendly_error(user_id: int, exc: Exception) -> str:
    lang = settings.get(user_id).language
    if isinstance(exc, RateLimitError):
        return ui_for_user(
            lang,
            "llm_quota",
        )
    if isinstance(exc, APIConnectionError):
        if _provider == "ollama":
            return ui_for_user(lang, "llm_ollama_down")
        return ui_for_user(lang, "llm_connection", error=str(exc))
    return ui_for_user(lang, "ai_error", error=str(exc))


async def ask_ai(channel_id: int, user_id: int, user_text: str) -> str:
    if _client is None:
        raise RuntimeError("LLM client not initialized")

    history.add(channel_id, "user", user_text)
    messages = [
        {"role": "system", "content": system_prompt_for(user_id)},
        *history.get(channel_id),
    ]

    log.info(
        "LLM request (provider=%s user=%s channel=%s lang=%s prompt_len=%d)",
        _provider,
        user_id,
        channel_id,
        settings.get(user_id).language,
        len(user_text),
    )
    log.debug("User text: %s", user_text[:500])

    started = time.perf_counter()

    def _call() -> str:
        response = _client.chat.completions.create(
            model=_model,
            messages=messages,
            temperature=0.7,
            max_tokens=800,
        )
        return (response.choices[0].message.content or "").strip()

    try:
        reply = await asyncio.wait_for(
            asyncio.to_thread(_call),
            timeout=float(LLM_TIMEOUT_SECONDS) + 10.0,
        )
    except asyncio.TimeoutError:
        log.error(
            "LLM timed out after %ss (provider=%s user=%s)",
            LLM_TIMEOUT_SECONDS,
            _provider,
            user_id,
        )
        raise RuntimeError(
            ui_for_user(settings.get(user_id).language, "llm_timeout")
        ) from None
    except Exception as exc:
        log.exception("LLM call failed (provider=%s)", _provider)
        raise RuntimeError(_friendly_error(user_id, exc)) from exc

    elapsed_ms = (time.perf_counter() - started) * 1000
    if not reply:
        log.warning("Empty LLM reply (user=%s channel=%s)", user_id, channel_id)
        reply = ui_for_user(settings.get(user_id).language, "llm_empty")

    history.add(channel_id, "assistant", reply)
    log.info(
        "LLM reply (provider=%s user=%s channel=%s reply_len=%d elapsed_ms=%.0f)",
        _provider,
        user_id,
        channel_id,
        len(reply),
        elapsed_ms,
    )
    log.debug("Reply text: %s", reply[:500])
    return reply[:MAX_REPLY_CHARS]


# Backwards compatibility
init_openai = init_llm
