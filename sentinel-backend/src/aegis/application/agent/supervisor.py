"""Supervisor Agent logic for generating execution plans."""

from typing import Any

from pydantic import BaseModel, Field

from aegis.application.agent.base import BaseAgent
from aegis.application.agent.models import AgentContext, AgentResult, AgentState
from aegis.domain.events import AgentEventType


class AgentTask(BaseModel):
    """Represents a specific task to be executed by a child agent."""

    agent_name: str
    dependencies: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)


class ExecutionPlan(BaseModel):
    """The directed acyclic graph (DAG) of agents to execute."""

    tasks: list[AgentTask] = Field(default_factory=list)


class SupervisorAgent(BaseAgent):
    """The entry point agent that analyzes the context and determines what needs to run.

    Currently implements a deterministic mocked execution plan. Later, this will
    use the Gemini API to dynamically determine the necessary specialized agents.
    """

    async def execute(self, context: AgentContext) -> AgentResult:
        """Formulates an execution plan and updates the shared context."""

        await self._emit_event(
            context=context,
            event_type=AgentEventType.PROGRESS,
            message="Analyzing repository context to formulate execution plan...",
        )

        # Mocked generation logic (represents time taken to call an LLM in the future)
        plan = ExecutionPlan(
            tasks=[
                AgentTask(
                    agent_name="repository_agent",
                    dependencies=[],
                    payload={"instruction": "Index the repository and build dependency graph."},
                ),
                AgentTask(
                    agent_name="security_agent",
                    dependencies=["repository_agent"],
                    payload={"instruction": "Scan for hardcoded secrets and SQL injections."},
                ),
                AgentTask(
                    agent_name="patch_agent",
                    dependencies=["security_agent"],
                    payload={
                        "instruction": "Generate deterministic patches for security findings."
                    },
                ),
            ]
        )

        # Mutate the shared state to hold the execution plan
        context.shared_state["execution_plan"] = plan.model_dump()

        await self._emit_event(
            context=context,
            event_type=AgentEventType.PROGRESS,
            message="Execution plan formulated successfully.",
            payload={"task_count": len(plan.tasks)},
        )

        return AgentResult(
            status=AgentState.COMPLETE,
            confidence=1.0,
            metadata={"plan_generated": True, "tasks": len(plan.tasks)},
        )
