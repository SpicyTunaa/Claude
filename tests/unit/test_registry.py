"""Registry / plugin-isolation tests — adding a source must be one file, zero core edits."""

from collections.abc import AsyncIterator

from leadengine.adapters import AdapterContext, available_adapters, register
from leadengine.adapters.base import SourceAdapter
from leadengine.core.models import AdapterMetadata, RawHit


def test_builtin_adapters_registered():
    adapters = available_adapters()
    assert "example" in adapters
    assert "hackernews" in adapters


def test_register_new_adapter_appears_without_core_changes():
    @register
    class DummySource(SourceAdapter):
        name = "dummy_test_source"

        def metadata(self) -> AdapterMetadata:
            return AdapterMetadata(name=self.name)

        async def discover(self, ctx: AdapterContext) -> AsyncIterator[RawHit]:
            yield RawHit(source=self.name, url="https://dummy.example")

    assert "dummy_test_source" in available_adapters()
