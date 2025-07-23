import ast
import operator
import math
import logging
from typing import Union
import re

logger = logging.getLogger(__name__)

class BasicCalculator:
    """Simple calculator for basic arithmetic operations."""
    
    # Define allowed operators
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
        ast.Mod: operator.mod,
    }
    
    # Define basic mathematical functions
    FUNCTIONS = {
        'abs': abs,
        'round': round,
        'sqrt': math.sqrt,
        'pow': pow,
        'pi': math.pi,
        'e': math.e,
    }
    
    def calculate(self, expression: str) -> str:
        """
        Safely evaluate a basic mathematical expression.
        
        Args:
            expression: Mathematical expression as a string
            
        Returns:
            Result as a formatted string
        """
        try:
            # Clean and validate the expression
            cleaned_expr = self._clean_expression(expression)
            
            if not cleaned_expr:
                return "Error: Empty or invalid expression"
            
            # Parse and evaluate the expression
            result = self._safe_eval(cleaned_expr)
            
            # Format the result
            formatted_result = self._format_result(result, expression)
            
            logger.info(f"Calculator: {expression} = {result}")
            return formatted_result
            
        except ZeroDivisionError:
            return f"Error: Division by zero in expression '{expression}'"
        except ValueError as e:
            return f"Error: Invalid value in expression '{expression}'"
        except Exception as e:
            logger.error(f"Calculator error: {e}")
            return f"Error: Could not evaluate expression '{expression}'"
    
    def _clean_expression(self, expression: str) -> str:
        """Clean and validate the input expression."""
        if not expression or not isinstance(expression, str):
            return ""
        
        # Remove whitespace
        cleaned = expression.replace(" ", "")
        
        # Replace common constants
        replacements = {
            'pi': str(math.pi),
            'e': str(math.e),
        }
        
        for old, new in replacements.items():
            cleaned = re.sub(r'\b' + old + r'\b', new, cleaned)
        
        return cleaned
    
    def _safe_eval(self, expression: str) -> Union[int, float]:
        """Safely evaluate the expression using AST."""
        try:
            node = ast.parse(expression, mode='eval')
            return self._eval_node(node.body)
        except SyntaxError:
            raise ValueError("Invalid syntax")
    
    def _eval_node(self, node) -> Union[int, float]:
        """Recursively evaluate an AST node."""
        if isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif isinstance(node, ast.Num):  # Python < 3.8
            return node.n
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            operator_func = self.OPERATORS.get(type(node.op))
            if operator_func is None:
                raise ValueError("Unsupported operator")
            return operator_func(left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            operator_func = self.OPERATORS.get(type(node.op))
            if operator_func is None:
                raise ValueError("Unsupported operator")
            return operator_func(operand)
        elif isinstance(node, ast.Call):
            func_name = node.func.id if isinstance(node.func, ast.Name) else None
            if func_name not in self.FUNCTIONS:
                raise ValueError(f"Unsupported function: {func_name}")
            
            args = [self._eval_node(arg) for arg in node.args]
            func = self.FUNCTIONS[func_name]
            return func(*args)
        elif isinstance(node, ast.Name):
            # Handle constants
            if node.id in self.FUNCTIONS and isinstance(self.FUNCTIONS[node.id], (int, float)):
                return self.FUNCTIONS[node.id]
            else:
                raise ValueError(f"Unsupported variable: {node.id}")
        else:
            raise ValueError("Unsupported operation")
    
    def _format_result(self, result: Union[int, float], original_expr: str) -> str:
        """Format the calculation result."""
        try:
            if isinstance(result, float):
                if result.is_integer():
                    formatted_result = str(int(result))
                else:
                    formatted_result = f"{result:.6g}"  # 6 significant digits
            else:
                formatted_result = str(result)
            
            return f"Calculation: {original_expr} = {formatted_result}"
            
        except Exception:
            return f"Calculation: {original_expr} = {result}"

# Create global instance
calculator = BasicCalculator()

def calculate_expression(expression: str) -> str:
    return calculator.calculate(expression)