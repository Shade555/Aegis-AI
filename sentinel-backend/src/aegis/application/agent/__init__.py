"""Core Agent Framework."""

from aegis.application.agent.base import BaseAgent
from aegis.application.agent.models import AgentContext, AgentResult, AgentState, WorkItem
from aegis.application.agent.patch import PatchGenerationAgent
from aegis.application.agent.ports import ConfigProvider, EventBus, Logger
from aegis.application.agent.registry import WorkItemRegistry
from aegis.application.agent.repository import RepositoryAgent, RepositoryManifest
from aegis.application.agent.supervisor import SupervisorAgent

__all__ = [
    "BaseAgent",
    "AgentContext",
    "AgentResult",
    "AgentState",
    "WorkItem",
    "EventBus",
    "Logger",
    "ConfigProvider",
    "WorkItemRegistry",
    "SupervisorAgent",
    "RepositoryAgent",
    "RepositoryManifest",
    "PatchGenerationAgent",
]
