import aiohttp
import logging
from datetime import datetime, date
from typing import List, Dict, Optional
from config import Config

logger = logging.getLogger(__name__)

class AgricultureAPIService:
    """Service to fetch data from various agriculture-related APIs"""
    
    def __init__(self):
        self.data_gov_api_key = Config.DATA_GOV_API_KEY
        self.openweather_api_key = Config.OPENWEATHER_API_KEY
        self.agmarknet_base = Config.AGMARKNET_API_BASE
    
    async def get_commodity_prices(
        self, 
        commodity: str, 
        state: Optional[str] = None,
        district: Optional[str] = None
    ) -> List[Dict]:
        """
        Fetch commodity prices from data.gov.in Agmarknet API
        
        Args:
            commodity: Name of commodity (e.g., "wheat", "rice")
            state: State name (optional)
            district: District name (optional)
            
        Returns:
            List of market price data
        """
        try:
            # Data.gov.in commodity price API endpoint
            url = f"{self.agmarknet_base}/9ef84268-d588-465a-a308-a864a43d0070"
            
            params = {
                "api-key": self.data_gov_api_key,
                "format": "json",
                "limit": 20
            }
            
            if commodity:
                params["filters[commodity]"] = commodity
            if state:
                params["filters[state]"] = state
            if district:
                params["filters[district]"] = district
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("records", [])
                    else:
                        logger.error(f"Commodity API error: {response.status}")
                        return []
        
        except Exception as e:
            logger.error(f"Error fetching commodity prices: {str(e)}")
            return []
    
    async def get_weather_forecast(
        self, 
        latitude: float, 
        longitude: float,
        days: int = 7
    ) -> Dict:
        """
        Get weather forecast using OpenWeather API
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            days: Number of days for forecast
            
        Returns:
            Weather forecast data
        """
        try:
            url = "https://api.openweathermap.org/data/2.5/forecast"
            
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.openweather_api_key,
                "units": "metric",
                "cnt": days * 8  # 3-hour intervals
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_weather_data(data)
                    else:
                        logger.error(f"Weather API error: {response.status}")
                        return {}
        
        except Exception as e:
            logger.error(f"Error fetching weather: {str(e)}")
            return {}
    
    def _process_weather_data(self, raw_data: Dict) -> Dict:
        """Process raw weather data into usable format"""
        try:
            forecasts = []
            for item in raw_data.get("list", []):
                forecasts.append({
                    "datetime": item.get("dt_txt"),
                    "temperature": item["main"]["temp"],
                    "humidity": item["main"]["humidity"],
                    "weather": item["weather"][0]["description"],
                    "wind_speed": item["wind"]["speed"],
                    "rain": item.get("rain", {}).get("3h", 0)
                })
            
            return {
                "city": raw_data.get("city", {}).get("name"),
                "forecasts": forecasts
            }
        except Exception as e:
            logger.error(f"Error processing weather data: {str(e)}")
            return {}
    
    async def get_current_weather(
        self, 
        city: str = None,
        latitude: float = None,
        longitude: float = None
    ) -> Dict:
        """
        Get current weather conditions
        
        Args:
            city: City name (optional)
            latitude: Location latitude (optional)
            longitude: Location longitude (optional)
            
        Returns:
            Current weather data
        """
        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            
            params = {
                "appid": self.openweather_api_key,
                "units": "metric"
            }
            
            if city:
                params["q"] = city
            elif latitude and longitude:
                params["lat"] = latitude
                params["lon"] = longitude
            else:
                return {}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "location": data.get("name"),
                            "temperature": data["main"]["temp"],
                            "humidity": data["main"]["humidity"],
                            "weather": data["weather"][0]["description"],
                            "wind_speed": data["wind"]["speed"],
                            "pressure": data["main"]["pressure"]
                        }
                    else:
                        logger.error(f"Weather API error: {response.status}")
                        return {}
        
        except Exception as e:
            logger.error(f"Error fetching current weather: {str(e)}")
            return {}
    
    async def search_mandi_prices(
        self,
        commodity: str,
        location: str
    ) -> List[Dict]:
        """
        Search for mandi (market) prices for a commodity
        
        Args:
            commodity: Commodity name
            location: Location (state/district)
            
        Returns:
            List of mandi price information
        """
        # This can be enhanced with more specific mandi APIs
        return await self.get_commodity_prices(commodity, state=location)
    
    async def get_soil_health_info(self, district: str, state: str) -> Dict:
        """
        Get soil health information (placeholder for future API integration)
        
        Args:
            district: District name
            state: State name
            
        Returns:
            Soil health data
        """
        # Placeholder for soil health card data API
        # This would integrate with actual soil health API when available
        return {
            "district": district,
            "state": state,
            "message": "Soil health data integration pending"
        }
    
    async def get_rainfall_data(
        self,
        latitude: float,
        longitude: float,
        days: int = 7
    ) -> Dict:
        """
        Get rainfall forecast data
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            days: Number of days
            
        Returns:
            Rainfall forecast
        """
        weather_data = await self.get_weather_forecast(latitude, longitude, days)
        
        if not weather_data:
            return {}
        
        rainfall_forecast = []
        for forecast in weather_data.get("forecasts", []):
            if forecast.get("rain", 0) > 0:
                rainfall_forecast.append({
                    "datetime": forecast["datetime"],
                    "rainfall_mm": forecast["rain"],
                    "probability": "High" if forecast["rain"] > 5 else "Medium"
                })
        
        return {
            "location": weather_data.get("city"),
            "rainfall_forecast": rainfall_forecast
        }

# Global agriculture API service instance
agriculture_api_service = AgricultureAPIService()