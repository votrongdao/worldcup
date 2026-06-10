"""Agentic core: event bus, run-context, agent registry."""
import pytest

from src.agents.base import TournamentRunContext
from src.agents.registry import AgentRegistry
from src.infra.memory import InMemoryBackend


@pytest.mark.asyncio
async def test_event_bus_history_is_ordered_and_scoped():
    b = InMemoryBackend()
    await b.emit("run-1", {"type": "a"})
    await b.emit("run-1", {"type": "b"})
    assert [e["type"] for e in await b.history("run-1")] == ["a", "b"]
    assert await b.history("run-2") == []
    assert len(await b.history("run-1", limit=1)) == 1


@pytest.mark.asyncio
async def test_run_context_emits_to_bus():
    b = InMemoryBackend()
    ctx = TournamentRunContext(seed=7, bus=b, topic="topic")
    await ctx.emit("phase", phase="group")
    assert await b.history("topic") == [{"type": "phase", "phase": "group"}]
    # A null bus is a safe no-op.
    await TournamentRunContext(7, None, "x").emit("noop")


def test_agent_registry_lookup_by_name():
    class Fake:
        name = "fake_agent"

    reg = AgentRegistry()
    a = Fake()
    reg.register(a)
    assert reg.get("fake_agent") is a
