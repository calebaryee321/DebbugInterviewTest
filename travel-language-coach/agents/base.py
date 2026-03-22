"""Abstract base class for all Travel Language Coach agents."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    """Base class that every agent in the Travel Language Coach must extend.

    Provides a common interface for agent identification, system prompt
    generation, and the core ``process`` entry-point.
    """

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Short machine-friendly name for this agent (e.g. ``'tutor'``)."""

    @property
    @abstractmethod
    def agent_role(self) -> str:
        """Human-readable description of the agent's responsibility."""

    @abstractmethod
    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Run the agent's main logic on *payload* and return a result dict.

        Parameters
        ----------
        payload:
            Arbitrary dictionary whose schema depends on the concrete agent.

        Returns
        -------
        Dict[str, Any]
            Result dictionary – structure varies per agent.
        """

    def get_system_prompt(self) -> str:
        """Return the LLM system prompt for this agent.

        Subclasses should override this to provide a role-specific prompt.
        The default implementation returns a generic prompt built from the
        agent's name and role.
        """
        return (
            f"You are the {self.agent_name} agent. "
            f"Your role: {self.agent_role}."
        )

    # ------------------------------------------------------------------
    # Placeholder for LLM integration
    # ------------------------------------------------------------------

    def _call_llm(self, system_prompt: str, user_message: str) -> str:
        """Send a request to the backing LLM and return its response.

        This is a **placeholder** – swap in a real API call (OpenAI,
        Anthropic, etc.) when credentials are available.

        Parameters
        ----------
        system_prompt:
            The system-level instruction for the LLM.
        user_message:
            The user-level content to send.

        Returns
        -------
        str
            The LLM's text response.
        """
        return (
            f"[LLM placeholder] system={system_prompt[:60]}… "
            f"user={user_message[:60]}…"
        )
