"""Deterministic mock response provider for the legacy chat interface."""
from .base import PHIGuard


class MockLLM:
    def __init__(self, system_name: str = "Qc Westgard Sentinel Agent"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        return (
            f"[{self.system_name} mock provider] This is a demonstration response; "
            "no model inference, clinical validation, or external lookup was performed. "
            f"Query received: {prompt[:60]!r}."
        )


class LLMFactory:
    """Only the explicitly implemented mock backend is available."""

    @staticmethod
    def create(provider: str = "mock", system_name: str = "Qc Westgard Sentinel Agent"):
        prov = str(provider).lower()
        if prov in ("mock", "deterministic", "test"):
            return MockLLM(system_name)
        raise ValueError(
            f"Unsupported model provider {provider!r}. "
            "Only the deterministic mock provider is implemented."
        )
