"""Calculator tool that provides basic arithmetic operations.

This tool performs basic calculations and can be used by agents.
"""

class Calculator:
    """Simple calculator tool with basic arithmetic operations."""
    
    @staticmethod
    def add(a: int, b: int) -> int:
        """Add two numbers together."""
        return a + b
    
    @staticmethod
    def subtract(a: int, b: int) -> int:
        """Subtract b from a."""
        return a - b
    
    @staticmethod
    def multiply(a: int, b: int) -> int:
        """Multiply two numbers together."""
        return a * b
    
    @staticmethod
    def divide(a: int, b: int) -> float:
        """Divide a by b.
        
        Raises:
            ZeroDivisionError: If b is zero.
        """
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return a / b

def calculate(a: int, b: int, operation: str) -> float:
    """Perform a calculation based on the specified operation.
    
    Args:
        a: First number
        b: Second number
        operation: One of 'add', 'subtract', 'multiply', 'divide'
        
    Returns:
        Result of the calculation
        
    Raises:
        ValueError: If operation is not supported
        ZeroDivisionError: If dividing by zero
    """
    calculator = Calculator()
    
    if operation == 'add':
        return calculator.add(a, b)
    elif operation == 'subtract':
        return calculator.subtract(a, b)
    elif operation == 'multiply':
        return calculator.multiply(a, b)
    elif operation == 'divide':
        return calculator.divide(a, b)
    else:
        raise ValueError(f"Unsupported operation: {operation}") 