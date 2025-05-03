"""Calculator Agent implementation that uses the calculator tool."""

import random
import logging
from typing import Any, Optional, Union, Tuple

from froge.agents.agent_base import BaseAgent, MonitoredAgentError
from froge.froge.tools.calculator import calculate

class CalculatorAgent(BaseAgent):
    """
    An agent that performs calculations using the calculator tool.
    
    This agent can be configured to occasionally produce errors or wrong results
    to demonstrate the MedicAgent's healing capabilities.
    """
    def __init__(self, agent_id: str, error_rate: float = 0.0, wrong_result_rate: float = 0.0):
        """
        Initialize the CalculatorAgent.
        
        Args:
            agent_id: Unique identifier for this agent
            error_rate: Probability (0.0-1.0) that the agent will raise an error
            wrong_result_rate: Probability (0.0-1.0) that the agent will return an incorrect result
        """
        super().__init__(agent_id)
        if not 0 <= error_rate <= 1:
            raise ValueError("error_rate must be between 0 and 1")
        if not 0 <= wrong_result_rate <= 1:
            raise ValueError("wrong_result_rate must be between 0 and 1")
            
        self.error_rate = error_rate
        self.wrong_result_rate = wrong_result_rate
        self._call_count = 0

    def run_task(self, a: int, b: int, operation: str = 'add') -> int:
        """
        Run a calculation task using the calculator tool.
        
        Args:
            a: First operand
            b: Second operand 
            operation: The type of calculation to perform ('add', 'subtract', 'multiply', 'divide')
            
        Returns:
            Result of the calculation
            
        Raises:
            MonitoredAgentError: If the operation fails or is unsupported,
                                 or if the simulated error occurs
        """
        self._call_count += 1
        self._logger.info(f"Running task: {a} {operation} {b} (call #{self._call_count})")

        # Simulate random failure based on error rate
        if random.random() < self.error_rate:
            error_msg = f"Simulated calculation error on call {self._call_count}"
            self._logger.warning(error_msg)
            raise MonitoredAgentError(error_msg, self.agent_id)

        # Use the calculator tool to perform the calculation
        try:
            result = calculate(a, b, operation)
        except ValueError as e:
            error_msg = f"Invalid operation: {operation}"
            self._logger.error(error_msg)
            raise MonitoredAgentError(error_msg, self.agent_id, original_exception=e)
        except ZeroDivisionError as e:
            error_msg = f"Cannot divide by zero: {a}/{b}"
            self._logger.error(error_msg)
            raise MonitoredAgentError(error_msg, self.agent_id, original_exception=e)
        except Exception as e:
            error_msg = f"Unexpected error during calculation: {str(e)}"
            self._logger.error(error_msg)
            raise MonitoredAgentError(error_msg, self.agent_id, original_exception=e)

        # Simulate producing a wrong result based on wrong_result_rate
        if random.random() < self.wrong_result_rate:
            correct_result = result
            # Introduce an error by adding or subtracting a small random value
            wrong_result = correct_result + random.randint(1, 5) * random.choice([-1, 1])
            self._logger.warning(f"Intentionally producing wrong result: {wrong_result} instead of {correct_result}")
            self.last_result = wrong_result
            return wrong_result

        self.last_result = result
        return result

    def is_result_valid(self, result: Any) -> bool:
        """
        Validate the calculation result.
        
        Args:
            result: The result to validate
            
        Returns:
            True if the result is valid, False otherwise
        """
        # Basic validation: check that the result is a number
        if not isinstance(result, (int, float)):
            self._logger.warning(f"Validation failed: Result '{result}' is not a number.")
            return False
            
        # Additional validation could be added here, such as:
        # - Bounds checking (e.g., result must be positive)
        # - Re-running the calculation to verify correctness
        # - Checking against expected ranges or business rules
            
        self._logger.debug(f"Validation passed for result: {result}")
        return True
        
    def verify_calculation(self, a: int, b: int, operation: str, expected_result: Optional[Union[int, float]] = None) -> Tuple[bool, str]:
        """
        Verify that a calculation gives the expected result.
        
        Args:
            a: First operand
            b: Second operand
            operation: The operation ('add', 'subtract', 'multiply', 'divide')
            expected_result: The expected result, or None to calculate it
            
        Returns:
            (is_valid, message): Whether the calculation is valid and a message
        """
        try:
            # Calculate the correct result using the calculator tool directly
            # This bypasses the error_rate and wrong_result_rate settings
            correct_result = calculate(a, b, operation)
            
            # If no expected result was provided, we're just testing if calculation works
            if expected_result is None:
                return True, f"Calculation works: {a} {operation} {b} = {correct_result}"
                
            # Otherwise, check if the expected result matches the calculated result
            if expected_result == correct_result:
                return True, f"Result {expected_result} is correct"
            else:
                return False, f"Expected {expected_result} but got {correct_result}"
                
        except Exception as e:
            return False, f"Calculation error: {str(e)}" 