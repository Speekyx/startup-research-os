"""Provider implementations.

**The ONLY place a provider SDK may be imported** (ADR-006). Business services
depend on the gateway abstraction; a lint rule and a tokenized test enforce that,
and both would fail if a vendor name appeared outside this package.

As it happens, no vendor SDK is imported here either. Both adapters speak their
provider's HTTP API through an injectable `HttpTransport`, which keeps
`uv.lock` free of vendor dependencies and makes the whole suite runnable with no
API key and no bill (Mission 0.4 §20). The reasoning is in `../transport.py`.

    anthropic.py  Messages API. Structured output via forced tool use
    gemini.py     generateContent. Structured output via responseSchema
    fake.py       test doubles: routing, retry, budget and validation paths

**Registering a real provider is a configuration decision, not an import.**
Nothing here is registered automatically: `LlmGateway.register` is called by
whoever assembles the application, and a tier with no configured provider raises
rather than silently downgrading (ADR-006).
"""

from .anthropic import AnthropicProvider
from .fake import EchoProvider, FailingProvider
from .gemini import GeminiProvider

__all__ = ["AnthropicProvider", "GeminiProvider", "EchoProvider", "FailingProvider"]
