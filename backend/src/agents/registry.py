"""Registries for agents and tools (simple in-process maps)."""
from __future__ import annotations
from typing import Dict
from .base import Agent, Tool


class ToolRegistry:
    def __init__(self) -> None: self._tools: Dict[str, Tool] = {}
    def register(self, tool: Tool) -> None: self._tools[tool.name] = tool
    def get(self, name: str) -> Tool: return self._tools[name]


class AgentRegistry:
    def __init__(self) -> None: self._agents: Dict[str, Agent] = {}
    def register(self, agent: Agent) -> None: self._agents[agent.name] = agent
    def get(self, name: str) -> Agent: return self._agents[name]
