import os
from app.core.config import Settings


def test_settings_default_values():
    s = Settings()
    assert s.APP_ENV == "development"
    assert s.CONFIDENCE_THRESHOLD == 0.8
    assert isinstance(s.LLM_FALLBACKS, list)
    assert "groq" in s.LLM_FALLBACKS


def test_configured_providers(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake_gemini_key")
    monkeypatch.setenv("GROQ_API_KEY", "")
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake_openrouter_key")

    s = Settings()
    providers = s.get_configured_providers()
    assert "gemini" in providers
    assert "groq" not in providers
    assert "openrouter" in providers
