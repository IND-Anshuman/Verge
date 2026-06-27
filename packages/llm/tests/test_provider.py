"""The provider contract: default is safe (null), and failures degrade not raise."""

from verge_llm import (
    Completion,
    LLMProvider,
    Message,
    NullProvider,
    OpenAICompatProvider,
    provider_from_env,
)


def test_default_is_null_provider() -> None:
    p = provider_from_env({})
    assert isinstance(p, NullProvider)
    assert p.healthy() is True


def test_null_provider_degrades_cleanly() -> None:
    p = NullProvider()
    c = p.complete([Message(role="user", content="summarize the convergence")])
    assert isinstance(c, Completion)
    assert c.degraded is True
    assert "summarize the convergence"[:10] in c.text


def test_providers_satisfy_protocol() -> None:
    assert isinstance(NullProvider(), LLMProvider)


def test_unreachable_remote_degrades_not_raises() -> None:
    # Points at an unroutable port; complete() must return degraded, never raise.
    p = OpenAICompatProvider(
        name="aimlapi",
        base_url="http://127.0.0.1:1/v1",
        api_key="x",
        default_model="claude-sonnet-4-5",
        timeout_s=0.2,
    )
    c = p.complete([Message(role="user", content="hi")])
    assert c.degraded is True
    assert "unreachable" in (c.reason or "")


def test_env_selects_aimlapi() -> None:
    p = provider_from_env({"VERGE_LLM_PROVIDER": "aimlapi", "AIMLAPI_API_KEY": "k"})
    assert p.name == "aimlapi"
