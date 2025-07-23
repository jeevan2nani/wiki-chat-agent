"""
Tools package for the Wiki-Powered Chat Agent.

This package contains various tools that the agent can use to provide
enhanced functionality beyond the basic Wikipedia search.
"""

from .weather import get_current_weather, get_weather_forecast
from .calculator import calculate_expression

__all__ = [
    'get_current_weather',
    'get_weather_forecast', 
    'calculate_expression'
] 