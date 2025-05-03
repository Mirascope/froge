#!/usr/bin/env python3
"""
Demo of the MedicAgent monitoring the CalculatorAgent.

This script demonstrates how the MedicAgent can monitor and heal
CalculatorAgents that occasionally fail or produce incorrect results.
"""

import logging
import random
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Import the agent implementations
from agents import MedicAgent, CalculatorAgent, AgentNotHealedError

def run_demo():
    """Run the demonstration of the MedicAgent with CalculatorAgents."""
    print("\n=== MEDIC AGENT DEMO ===")
    print("This demo shows how the MedicAgent monitors and heals other agents.")
    
    # Create a set of calculator agents with different failure patterns
    agent_reliable = CalculatorAgent(agent_id="Calc_Reliable")
    # This agent fails ~50% of the time on the first try, but might recover on retry
    agent_flaky_error = CalculatorAgent(agent_id="Calc_FlakyError", error_rate=0.5)
    # This agent succeeds but gives wrong results ~60% of the time
    agent_flaky_result = CalculatorAgent(agent_id="Calc_FlakyResult", wrong_result_rate=0.6)
    # This agent will always raise an error
    agent_hopeless = CalculatorAgent(agent_id="Calc_Hopeless", error_rate=1.0)

    # Set up the medic agent to monitor these calculator agents
    medic = MedicAgent(
        agents_to_monitor=[
            agent_reliable,
            agent_flaky_error,
            agent_flaky_result,
            agent_hopeless
        ],
        max_retries=2,  # Allow 2 retries (total 3 attempts)
        retry_delay_seconds=0.5
    )

    # Define tasks for each agent to perform
    tasks_for_checkup = {
        "Calc_Reliable": {'args': (10, 5), 'kwargs': {'operation': 'add'}},
        "Calc_FlakyError": {'args': (100, 1), 'kwargs': {'operation': 'subtract'}},
        "Calc_FlakyResult": {'args': (7, 8), 'kwargs': {'operation': 'add'}},
        # Hopeless agent will always fail regardless of operation
        "Calc_Hopeless": {'args': (1, 1), 'kwargs': {'operation': 'add'}}
    }

    # Run the health checkup
    print("\n--- MEDIC AGENT: STARTING CHECKUP ---")
    try:
        medic.perform_checkup(task_details=tasks_for_checkup)
        print("\n--- MEDIC AGENT: CHECKUP COMPLETED SUCCESSFULLY ---")
    except AgentNotHealedError as e:
        print(f"\n--- MEDIC AGENT: CHECKUP HALTED ---")
        print(f"Reason: Agent '{e.agent_id}' could not be healed.")
        final_error = getattr(e, 'last_error', 'Unknown Error')
        print(f"Last error reported for this agent: {final_error}")
    except Exception as e:
        print(f"\n--- MEDIC AGENT: AN UNEXPECTED ERROR OCCURRED ---")
        print(f"Error: {type(e).__name__}: {e}")
        logging.exception("Unexpected error during checkup execution:")

    # Display final status of all agents
    print("\n--- FINAL AGENT STATUS ---")
    for agent_id, agent in medic.agents.items():
        status = "Unknown"
        
        try:
            # Determine status based on last error and result validity
            if agent.last_error is not None:
                status = "Sick (Error)"
            # Check validity only if there wasn't an error and a result exists
            elif agent.last_result is not None:
                if agent.is_result_valid(agent.last_result):
                    status = "Healthy"
                else:
                    status = "Sick (Invalid Result)"
            else:
                # No error, no result likely means the agent wasn't run
                status = "Healthy (or Not Run)"
        except Exception as status_err:
            # Catch errors during status check itself
            status = f"Error checking status: {status_err}"

        print(f"Agent '{agent_id}': Status={status}")
        print(f"  - Last Result: {getattr(agent, 'last_result', 'N/A')}")
        print(f"  - Last Error: {getattr(agent, 'last_error', 'N/A')}")
        print(f"  - Consecutive Failures: {medic.consecutive_failures.get(agent_id, 'N/A')}")

if __name__ == "__main__":
    run_demo() 