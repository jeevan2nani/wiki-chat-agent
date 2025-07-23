import requests
import os
import logging
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

class WeatherTool:
    """Tool for fetching live weather information."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        self.base_url = "http://api.openweathermap.org/data/2.5"
        
        if not self.api_key:
            logger.warning("OPENWEATHER_API_KEY not set.")
    
    def get_weather(self, location: str) -> str:
        """
        Get current weather for a location.
        Args:
            location: City name, e.g., "London", "New York", "Tokyo"
        Returns:
            Formatted weather information as a string
        """
        try:
            if not self.api_key:
                return f"Sorry, I couldn't fetch weather data for {location}. Please check the location name and try again."
            
            # Get current weather
            url = f"{self.base_url}/weather"
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "metric"  # Use Celsius
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return self._format_weather_response(data)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Weather API request failed: {e}")
            return f"Sorry, I couldn't fetch weather data for {location}. Please check the location name and try again."
        except Exception as e:
            logger.error(f"Weather tool error: {e}")
            return f"An error occurred while fetching weather data: {str(e)}"
    
    def get_forecast(self, location: str, days: int = 5) -> str:
        """
        Get weather forecast for a location.
        
        Args:
            location: City name
            days: Number of days (1-5)
            
        Returns:
            Formatted forecast information as a string
        """
        try:
            if not self.api_key:
                return f"Sorry, I couldn't fetch forecast data for {location}. Please check the location name and try again."
            
            # Get 5-day forecast
            url = f"{self.base_url}/forecast"
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "metric",
                "cnt": min(days * 8, 40)  # 8 forecasts per day (3-hour intervals)
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return self._format_forecast_response(data, days)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Weather forecast API request failed: {e}")
            return f"Sorry, I couldn't fetch forecast data for {location}. Please check the location name and try again."
        except Exception as e:
            logger.error(f"Weather forecast tool error: {e}")
            return f"An error occurred while fetching forecast data: {str(e)}"
    
    def _format_weather_response(self, data: Dict[str, Any]) -> str:
        """Format the weather API response into a readable string."""
        try:
            city = data["name"]
            country = data["sys"]["country"]
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            pressure = data["main"]["pressure"]
            description = data["weather"][0]["description"].title()
            wind_speed = data["wind"]["speed"]
            
            weather_report = f"""Current Weather for {city}, {country}:
            
Temperature: {temp}°C (feels like {feels_like}°C)
Conditions: {description}
Humidity: {humidity}%
Pressure: {pressure} hPa
Wind Speed: {wind_speed} m/s
            """
            
            return weather_report.strip()
            
        except KeyError as e:
            logger.error(f"Missing key in weather response: {e}")
            return "Weather data received but couldn't parse it properly."
    
    def _format_forecast_response(self, data: Dict[str, Any], days: int) -> str:
        """Format the forecast API response into a readable string."""
        try:
            city = data["city"]["name"]
            country = data["city"]["country"]
            forecasts = data["list"]
            
            forecast_report = f"{days}-Day Weather Forecast for {city}, {country}:\n\n"
            
            # Group forecasts by day
            daily_forecasts = {}
            for forecast in forecasts:
                date = forecast["dt_txt"].split()[0]
                if date not in daily_forecasts:
                    daily_forecasts[date] = []
                daily_forecasts[date].append(forecast)
            
            # Take first forecast for each day
            for i, (date, day_forecasts) in enumerate(list(daily_forecasts.items())[:days]):
                forecast = day_forecasts[0]  # Take first forecast of the day
                temp = forecast["main"]["temp"]
                description = forecast["weather"][0]["description"].title()
                
                forecast_report += f"{date}: {temp}°C - {description}\n"
            
            return forecast_report.strip()
            
        except KeyError as e:
            logger.error(f"Missing key in forecast response: {e}")
            return "Forecast data received but couldn't parse it properly."
    
# Create global instance
weather_tool = WeatherTool()

def get_current_weather(location: str) -> str:
    """Get current weather for a location."""
    return weather_tool.get_weather(location)

def get_weather_forecast(location_and_days: str) -> str:
    """Get weather forecast. Format: 'location' or 'location, days'"""
    try:
        parts = location_and_days.split(",")
        location = parts[0].strip()
        days = int(parts[1].strip()) if len(parts) > 1 else 3
        days = max(1, min(days, 5))
        return weather_tool.get_forecast(location, days)
    except:
        return weather_tool.get_forecast(location_and_days.strip(), 3) 