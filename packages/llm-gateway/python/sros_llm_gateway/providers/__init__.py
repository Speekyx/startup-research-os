"""Provider implementations.

The ONLY place a provider SDK may be imported. Business services depend on the
gateway abstraction (ADR-006), and a lint rule plus a test enforce that.

Mission 0.2 ships no real provider: interfaces, configuration and test doubles
only. No external API call is made.
"""

from .fake import EchoProvider, FailingProvider

__all__ = ["EchoProvider", "FailingProvider"]
