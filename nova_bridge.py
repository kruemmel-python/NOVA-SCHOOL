from __future__ import annotations

from dataclasses import dataclass

from .embedded_nova import (
    EmbeddedNovaAIProviderRuntime,
    EmbeddedSecurityPlane,
    EmbeddedToolSandbox,
)


@dataclass(slots=True)
class NovaBridge:
    SecurityPlane: type
    ToolSandbox: type
    NovaAIProviderRuntime: type
    source: str = "embedded"


def load_nova_bridge() -> NovaBridge:
    return NovaBridge(
        SecurityPlane=EmbeddedSecurityPlane,
        ToolSandbox=EmbeddedToolSandbox,
        NovaAIProviderRuntime=EmbeddedNovaAIProviderRuntime,
        source="embedded",
    )
