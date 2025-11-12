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
        Fetch commodity prices from multiple sources with fallback mechanism:
        1. Try eNAM API (primary source)
        2. Fallback to data.gov.in daily mandi prices API
        
        Args:
            commodity: Name of commodity (e.g., "wheat", "rice")
            state: State name (optional)
            district: District name (optional)
            
        Returns:
            List of market price data
        """
        # Try eNAM API first
        enam_data = await self._get_enam_prices(commodity, state, district)
        
        if enam_data and len(enam_data) > 0:
            logger.info(f"✅ Successfully fetched {len(enam_data)} records from eNAM API")
            return enam_data
        
        # Fallback to data.gov.in daily mandi prices
        logger.warning("⚠️ eNAM API returned no data, trying data.gov.in fallback...")
        datagov_data = await self._get_datagov_mandi_prices(commodity, state, district)
        
        if datagov_data and len(datagov_data) > 0:
            logger.info(f"✅ Successfully fetched {len(datagov_data)} records from data.gov.in fallback API")
            return datagov_data
        
        logger.error("❌ Both APIs failed to return data")
        return []
    
    async def _get_enam_prices(
        self,
        commodity: str,
        state: Optional[str] = None,
        district: Optional[str] = None
    ) -> List[Dict]:
        """
        Fetch commodity prices from eNAM via data.gov.in Agmarknet API
        
        Args:
            commodity: Name of commodity
            state: State name (optional)
            district: District name (optional)
            
        Returns:
            List of market price data from eNAM
        """
        try:
            # Data.gov.in Agmarknet API endpoint (eNAM data)
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
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        records = data.get("records", [])
                        if records:
                            logger.info(f"eNAM API returned {len(records)} records")
                        return records
                    else:
                        logger.warning(f"eNAM API error: HTTP {response.status}")
                        return []
        
        except Exception as e:
            logger.error(f"Error fetching eNAM prices: {str(e)}")
            return []
    
    async def _get_datagov_mandi_prices(
        self,
        commodity: Optional[str] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
        market: Optional[str] = None
    ) -> List[Dict]:
        """
        Fetch current daily mandi prices from data.gov.in as fallback
        
        This API provides current daily prices from various mandis across India.
        
        Args:
            commodity: Commodity name (optional)
            state: State name (optional)
            district: District name (optional)
            market: Market/Mandi name (optional)
            
        Returns:
            List of daily mandi price data
        """
        try:
            # Data.gov.in Daily Mandi Prices API
            url = f"{self.agmarknet_base}/9ef84268-d588-465a-a308-a864a43d0070"
            
            params = {
                "api-key": self.data_gov_api_key,
                "format": "json",
                "limit": 20,
                "offset": 0
            }
            
            # Add filters if provided
            if commodity:
                params["filters[commodity]"] = commodity
            if state:
                params["filters[state.keyword]"] = state
            if district:
                params["filters[district]"] = district
            if market:
                params["filters[market]"] = market
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        records = data.get("records", [])
                        
                        if records:
                            logger.info(f"Data.gov.in mandi API returned {len(records)} records")
                            # Normalize the data format to match expected structure
                            return self._normalize_mandi_data(records)
                        else:
                            logger.warning("Data.gov.in mandi API returned empty records")
                        return records
                    elif response.status == 403:
                        logger.error("Data.gov.in API: Forbidden - Check API key")
                        return []
                    elif response.status == 400:
                        logger.error("Data.gov.in API: Bad request - Check parameters")
                        return []
                    else:
                        logger.warning(f"Data.gov.in mandi API error: HTTP {response.status}")
                        return []
        
        except Exception as e:
            logger.error(f"Error fetching data.gov.in mandi prices: {str(e)}")
            return []
    
    def _normalize_mandi_data(self, records: List[Dict]) -> List[Dict]:
        """
        Normalize data.gov.in mandi data to standard format
        
        Args:
            records: Raw records from data.gov.in API
            
        Returns:
            Normalized list of price records
        """
        normalized = []
        
        for record in records:
            try:
                # Extract and normalize fields
                normalized_record = {
                    "state": record.get("state", ""),
                    "district": record.get("district", ""),
                    "market": record.get("market", ""),
                    "commodity": record.get("commodity", ""),
                    "variety": record.get("variety", ""),
                    "grade": record.get("grade", ""),
                    "arrival_date": record.get("arrival_date", ""),
                    "min_price": self._safe_float(record.get("min_price", 0)),
                    "max_price": self._safe_float(record.get("max_price", 0)),
                    "modal_price": self._safe_float(record.get("modal_price", 0)),
                    "price_date": record.get("price_date", ""),
                    "source": "data.gov.in"
                }
                normalized.append(normalized_record)
            except Exception as e:
                logger.warning(f"Error normalizing record: {str(e)}")
                continue
        
        return normalized
    
    def _safe_float(self, value) -> float:
        """Safely convert value to float"""
        try:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                # Remove commas and convert
                cleaned = value.replace(",", "").strip()
                return float(cleaned) if cleaned else 0.0
            return 0.0
        except (ValueError, TypeError):
            return 0.0
    
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
    
    async def get_daily_mandi_prices(
        self,
        commodity: Optional[str] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
        market: Optional[str] = None,
        variety: Optional[str] = None,
        grade: Optional[str] = None
    ) -> List[Dict]:
        """
        Get current daily mandi prices directly from data.gov.in API
        
        This method provides direct access to the daily mandi prices API
        with all available filter options.
        
        Args:
            commodity: Commodity name (e.g., "Wheat", "Rice")
            state: State name
            district: District name
            market: Market/Mandi name
            variety: Variety of commodity
            grade: Grade of commodity
            
        Returns:
            List of current daily mandi prices
        """
        try:
            url = f"{self.agmarknet_base}/9ef84268-d588-465a-a308-a864a43d0070"
            
            params = {
                "api-key": self.data_gov_api_key,
                "format": "json",
                "limit": 50,
                "offset": 0
            }
            
            # Add all available filters
            if commodity:
                params["filters[commodity]"] = commodity
            if state:
                params["filters[state.keyword]"] = state
            if district:
                params["filters[district]"] = district
            if market:
                params["filters[market]"] = market
            if variety:
                params["filters[variety]"] = variety
            if grade:
                params["filters[grade]"] = grade
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status == 200:
                        data = await response.json()
                        records = data.get("records", [])
                        logger.info(f"Daily mandi prices: {len(records)} records fetched")
                        return self._normalize_mandi_data(records)
                    else:
                        logger.error(f"Daily mandi API error: HTTP {response.status}")
                        return []
        
        except Exception as e:
            logger.error(f"Error fetching daily mandi prices: {str(e)}")
            return []
    
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