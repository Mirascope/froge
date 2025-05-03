import logging
import time
import random # For example usage simulation
from typing import Any, List, Dict, Callable, Optional
import collections # Needed for duplicate check in MedicAgent init

# Import base classes and exceptions from the new file
# This should be at the top level
from agent_base import BaseAgent, MonitoredAgentError, AgentNotHealedError

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class MedicAgent:
    """
    Monitors other agents, detects issues ('sickness'), attempts recovery ('healing'),
    and reports persistent failures.
    """

    def __init__(
        self,
        agents_to_monitor: List[BaseAgent], # BaseAgent is now imported
        max_retries: int = 2,
        retry_delay_seconds: float = 1.0
        ):
        """
        Initializes the MedicAgent.

        Args:
            agents_to_monitor: A list of agent instances (inheriting from BaseAgent) to monitor.
            max_retries: Maximum number of times to retry a failing agent's task (0 means one attempt only).
            retry_delay_seconds: Time to wait between retry attempts.
        """
        if max_retries < 0:
            raise ValueError("max_retries cannot be negative.")

        self.agents: Dict[str, BaseAgent] = {agent.agent_id: agent for agent in agents_to_monitor}
        if len(self.agents) != len(agents_to_monitor):
             duplicate_ids = [item for item, count in collections.Counter(a.agent_id for a in agents_to_monitor).items() if count > 1]
             raise ValueError(f"Duplicate agent IDs found: {duplicate_ids}")

        self.max_retries = max_retries
        self.retry_delay = retry_delay_seconds
        # Tracks consecutive failures for escalation
        self.consecutive_failures: Dict[str, int] = {agent_id: 0 for agent_id in self.agents}
        self._logger = logging.getLogger(self.__class__.__name__)

    def _is_sick(self, agent: BaseAgent, result: Any, error: Optional[Exception]) -> bool: # BaseAgent imported
        """
        Internal function to determine if an agent is 'sick' after a task attempt.

        An agent is considered sick if:
        1. The task execution resulted in an error (`error` is not None).
        2. The task completed without error, but the result is deemed invalid
           by the agent's `is_result_valid` method.

        Args:
            agent: The agent instance being checked.
            result: The result from the task attempt (None if error occurred).
            error: The exception raised during the task attempt (None if successful).

        Returns:
            True if the agent is considered sick, False otherwise.
        """
        if error:
            # Use the agent's specific logger if available, otherwise use the Medic's
            agent_logger = getattr(agent, '_logger', self._logger)
            agent_logger.warning(f"Agent '{agent.agent_id}' is sick. Reason: Task Error - {type(error).__name__}: {error}")
            return True

        # No error, check result validity
        try:
            is_valid = agent.is_result_valid(result)
            if not is_valid:
                agent_logger = getattr(agent, '_logger', self._logger)
                agent_logger.warning(f"Agent '{agent.agent_id}' is sick. Reason: Invalid Result - Result: {result}")
                return True
        except Exception as validation_error:
             agent_logger = getattr(agent, '_logger', self._logger)
             agent_logger.error(f"Agent '{agent.agent_id}' is sick. Reason: Validation Check Error - {type(validation_error).__name__}: {validation_error}")
             # Treat validation errors as sickness
             agent.last_error = validation_error
             return True


        # If no error and result is valid, agent is healthy for this run
        agent_logger = getattr(agent, '_logger', self._logger)
        agent_logger.debug(f"Agent '{agent.agent_id}' appears healthy for this run.")
        return False

    def _attempt_task_run(self, agent: BaseAgent, *args, **kwargs) -> tuple[Any | None, Exception | None]: # BaseAgent imported
        """Safely attempts to run the agent's task, capturing result or error."""
        result = None
        error = None
        agent_logger = getattr(agent, '_logger', self._logger)
        try:
            agent_logger.debug(f"Attempting task for agent '{agent.agent_id}'...")
            result = agent.run_task(*args, **kwargs)
            agent.last_result = result
            agent.last_error = None # Clear previous error on success
            agent_logger.debug(f"Agent '{agent.agent_id}' task attempt successful.")
        except MonitoredAgentError as e: # MonitoredAgentError imported
            agent_logger.warning(f"Agent '{agent.agent_id}' task attempt failed (MonitoredAgentError): {e}")
            error = e
            agent.last_result = None
            agent.last_error = e
        except Exception as e:
            # Catch unexpected errors during task execution
            self._logger.error(f"Agent '{agent.agent_id}' task attempt failed unexpectedly: {type(e).__name__}: {e}", exc_info=True)
            # Wrap unexpected errors for consistent handling
            error = MonitoredAgentError(f"Unexpected task error: {e}", agent.agent_id, original_exception=e) # MonitoredAgentError imported
            agent.last_result = None
            agent.last_error = error # Store the wrapped error
        return result, error

    def _heal_agent(self, agent: BaseAgent, *args, **kwargs) -> bool: # BaseAgent imported
        """
        Attempts to heal a sick agent by rerunning its task up to max_retries.

        Args:
            agent: The sick agent instance.
            *args, **kwargs: Arguments to pass to the agent's run_task method for retries.

        Returns:
            True if the agent becomes healthy within the retry limit, False otherwise.
        """
        agent_id = agent.agent_id
        self._logger.info(f"Attempting to heal agent '{agent_id}' (Max Retries: {self.max_retries})...")

        # Use a failure counter local to this healing attempt
        current_attempt_failures = 0

        for attempt in range(self.max_retries):
            retry_num = attempt + 1
            self._logger.info(f"Healing attempt {retry_num}/{self.max_retries} for agent '{agent_id}'...")

            if self.retry_delay > 0:
                time.sleep(self.retry_delay)

            result, error = self._attempt_task_run(agent, *args, **kwargs)

            if not self._is_sick(agent, result, error):
                self._logger.info(f"Agent '{agent_id}' successfully healed after {retry_num} retries.")
                # Reset the main consecutive failure count only on successful healing
                if agent_id in self.consecutive_failures:
                    self.consecutive_failures[agent_id] = 0
                return True # Healed successfully

            # Agent is still sick after this attempt
            current_attempt_failures += 1
            # Update the main consecutive failure count
            if agent_id in self.consecutive_failures:
                 self.consecutive_failures[agent_id] += 1
            else:
                 # Should not happen if agent was added correctly, but initialize defensively
                 self.consecutive_failures[agent_id] = current_attempt_failures + 1 # +1 for the initial failure

        # Exhausted all retries
        self._logger.error(f"Agent '{agent_id}' failed to heal after {self.max_retries} retries.")
        return False # Healing failed

    def _diagnose_and_report(self, agent: BaseAgent): # BaseAgent imported
        """
        Diagnoses a persistently failing agent and reports it (escalation).

        Currently logs a critical error and raises AgentNotHealedError.
        This could be extended to notify monitoring systems, etc.

        Args:
            agent: The agent that could not be healed.
        """
        agent_id = agent.agent_id
        last_error_info = agent.last_error or "Unknown (possibly invalid result without error)"
        consecutive_fails = self.consecutive_failures.get(agent_id, self.max_retries + 1) # Get count or assume max + initial failure

        report = (
            f"Diagnosis Report for Persistently Sick Agent '{agent_id}':\n"
            f"  Status: Unhealable after {consecutive_fails} consecutive failures (max retries: {self.max_retries}).\n"
            f"  Last Recorded Error: {type(last_error_info).__name__}: {last_error_info}\n"
            f"  Last Recorded Result: {getattr(agent, 'last_result', 'N/A')}\n"
            f"Escalating issue for agent '{agent_id}'."
        )
        self._logger.critical(report)

        # Raise an exception to signal the failure to the upper level/caller
        raise AgentNotHealedError( # AgentNotHealedError imported
            f"Agent '{agent_id}' could not be healed.",
            agent_id=agent_id,
            last_error=agent.last_error
        )

    def perform_checkup(self, task_details: Dict[str, Dict[str, Any]] = None):
        """
        Performs a health checkup on all monitored agents.

        For each agent, it attempts the task. If the agent is sick,
        it attempts healing. If healing fails, it diagnoses and reports.

        Args:
            task_details: Optional dictionary mapping agent_id to its task arguments.
                          Example: {'agent_id_1': {'args': (arg1,), 'kwargs': {'kwarg1': val1}}}
                          If an agent_id is missing, its task is run without arguments.

        Raises:
            AgentNotHealedError: If any agent fails healing and requires escalation.
                                  The checkup stops when the first agent cannot be healed.
                                  Modify this behavior if needed (e.g., collect all failures).
        """
        if task_details is None:
            task_details = {}

        self._logger.info(f"Starting checkup for {len(self.agents)} agents...")
        all_healthy_or_healed = True

        for agent_id, agent in self.agents.items():
            details = task_details.get(agent_id, {})
            args = details.get('args', ())
            kwargs = details.get('kwargs', {})

            self._logger.info(f"--- Checking Agent: {agent_id} ---")
            # Reset consecutive failure count at the start of *this* checkup cycle for the agent
            # The healing loop manages its own retry count internally based on this initial count.
            if agent_id in self.consecutive_failures:
                self.consecutive_failures[agent_id] = 0
            else:
                 self._logger.warning(f"Agent ID '{agent_id}' not found in consecutive_failures tracking at checkup start. Initializing.")
                 self.consecutive_failures[agent_id] = 0


            result, error = self._attempt_task_run(agent, *args, **kwargs)

            if self._is_sick(agent, result, error):
                # Mark the initial failure for this checkup cycle
                self.consecutive_failures[agent_id] = 1

                # Attempt to heal the agent
                healed = self._heal_agent(agent, *args, **kwargs) # _heal_agent increments consecutive_failures internally on failed retries

                if not healed:
                    all_healthy_or_healed = False
                    # Diagnose, report, and escalate (raises AgentNotHealedError)
                    self._diagnose_and_report(agent)
                    # Note: _diagnose_and_report currently raises, stopping the checkup.
            else:
                # Agent was healthy on the first attempt of this checkup
                 self.consecutive_failures[agent_id] = 0 # Ensure it's reset
                 agent_logger = getattr(agent, '_logger', self._logger)
                 agent_logger.info(f"Agent '{agent_id}' is healthy.")

        if all_healthy_or_healed:
             self._logger.info("Checkup complete. All monitored agents are healthy or were successfully healed.")
        # No 'else' needed here, as failure causes an exception or early exit normally

# --- Example Usage ---
# CalculatorAgent class definition is removed from here.
# It is now located in froge/froge/tools/calculator_agent.py

if __name__ == "__main__":
    # Import the agent specifically for the demo
    # Ensure froge directory is in the Python path or run from the project root
    try:
        from froge.froge.tools.calculator_agent import CalculatorAgent
    except ImportError as e:
        print(f"Error importing CalculatorAgent: {e}")
        print("Please ensure medic_agent.py is run from the project root directory containing 'agent_base.py' and the 'froge' directory.")
        print("and the file 'froge/froge/tools/calculator_agent.py' exists.")
        import sys
        sys.exit(1)


    # --- Setup Agents ---
    agent_reliable = CalculatorAgent(agent_id="Calc_Reliable")
    # This agent fails ~50% of the time on the first try, but might recover on retry
    agent_flaky_error = CalculatorAgent(agent_id="Calc_FlakyError", error_rate=0.5)
    # This agent succeeds but gives wrong results ~60% of the time
    agent_flaky_result = CalculatorAgent(agent_id="Calc_FlakyResult", wrong_result_rate=0.6)
    # This agent will always raise an error (error_rate=1.0)
    agent_hopeless = CalculatorAgent(agent_id="Calc_Hopeless", error_rate=1.0)

    # --- Setup Medic ---
    medic = MedicAgent(
        agents_to_monitor=[
            agent_reliable,
            agent_flaky_error,
            agent_flaky_result,
            agent_hopeless
        ],
        max_retries=2, # Allow 2 retries (total 3 attempts)
        retry_delay_seconds=0.5
    )

    # --- Define Tasks ---
    tasks_for_checkup = {
        "Calc_Reliable": {'args': (10, 5), 'kwargs': {'operation': 'add'}},
        "Calc_FlakyError": {'args': (100, 1), 'kwargs': {'operation': 'subtract'}},
        "Calc_FlakyResult": {'args': (7, 8), 'kwargs': {'operation': 'add'}},
        # Hopeless agent tries a valid operation but is configured to always fail
        "Calc_Hopeless": {'args': (1, 1), 'kwargs': {'operation': 'add'}} # error_rate is 1.0
    }

    # --- Run Checkup ---
    print("\n--- MEDIC AGENT: STARTING CHECKUP ---")
    try:
        medic.perform_checkup(task_details=tasks_for_checkup)
        print("\n--- MEDIC AGENT: CHECKUP COMPLETED (No unhealable agents found) ---")
    except AgentNotHealedError as e:
        print(f"\n--- MEDIC AGENT: CHECKUP HALTED ---")
        print(f"Reason: Agent '{e.agent_id}' could not be healed.")
        # Display the final error that prevented healing
        final_error = getattr(e, 'last_error', 'Unknown Error')
        print(f"Last error reported for this agent: {type(final_error).__name__}: {final_error}")
    except Exception as e:
        print(f"\n--- MEDIC AGENT: An unexpected error occurred during checkup ---")
        print(f"Error: {type(e).__name__}: {e}")
        logging.exception("Unexpected error during checkup execution:")


    print("\n--- FINAL AGENT STATUS ---")
    for agent_id, agent in medic.agents.items():
        status = "Unknown"
        agent_last_result = getattr(agent, 'last_result', None)
        agent_last_error = getattr(agent, 'last_error', None)

        try:
            # Determine status based on last error and result validity
            if agent_last_error is not None:
                status = "Sick (Error)"
            # Check validity only if there wasn't an error and a result exists
            elif agent_last_result is not None:
                # We need to handle potential errors within is_result_valid itself
                try:
                    if agent.is_result_valid(agent_last_result):
                        status = "Healthy"
                    else:
                        status = "Sick (Invalid Result)"
                except Exception as valid_err:
                    status = f"Sick (Validation Error: {valid_err})"

            else:
                # No error, no result likely means the agent wasn't run or checkup halted early
                 # Check consecutive failures to distinguish
                 if medic.consecutive_failures.get(agent_id, 0) > 0:
                      status = "Sick (Checkup Halted Before Completion?)"
                 else:
                      status = "Healthy (or Not Run/Halted Early)"


        except Exception as status_err:
            # Catch unexpected errors during status check itself
            status = f"Error checking status: {status_err}"

        print(f"Agent '{agent_id}': Status={status}")
        print(f"  - Last Result: {agent_last_result if agent_last_result is not None else 'N/A'}")
        print(f"  - Last Error: {agent_last_error if agent_last_error is not None else 'N/A'}")
        print(f"  - Consecutive Failures Recorded by Medic: {medic.consecutive_failures.get(agent_id, 'N/A')}") 