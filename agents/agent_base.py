"""Base agent definitions and exception classes for the agent system."""

from typing import Any, Optional
import logging

class MonitoredAgentError(Exception):
    """Custom exception for errors explicitly raised by monitored agents during tasks."""
    def __init__(self, message: str, agent_id: str, original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.agent_id = agent_id
        self.original_exception = original_exception

class AgentNotHealedError(Exception):
    """Raised by the MedicAgent when it fails to heal an agent after retries."""
    def __init__(self, message: str, agent_id: str, last_error: Optional[Exception]):
        super().__init__(message)
        self.agent_id = agent_id
        self.last_error = last_error

class BaseAgent:
    """
    Abstract base class for agents that the MedicAgent can monitor.
    Subclasses must implement run_task and may override is_result_valid.
    """
    def __init__(self, agent_id: str):
        if not agent_id:
            raise ValueError("Agent ID cannot be empty.")
        self.agent_id = agent_id
        self.last_error: Optional[Exception] = None
        self.last_result: Any = None
        # Configure logger
        self._logger = logging.getLogger(f"{self.__class__.__name__}[{self.agent_id}]")

    def run_task(self, *args, **kwargs) -> Any:
        """
        Executes the agent's primary task.
        Should return the task result upon success.
        Should raise MonitoredAgentError or a subclass on failure to signal the issue clearly.
        """
        raise NotImplementedError("Subclasses must implement run_task")

    def is_result_valid(self, result: Any) -> bool:
        """
        Validates the result produced by run_task.
        This acts as a 'loyalty check' or quality control.

        Args:
            result: The result returned by a successful run_task execution.

        Returns:
            True if the result is considered valid/correct/high-quality, False otherwise.
        """
        # Default: Any result from a non-erroring task is considered valid.
        # Subclasses should override this for meaningful validation.
        self._logger.debug(f"Performing default validation for result: {result}")
        return True

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(agent_id='{self.agent_id}')>" 