from pydantic import BaseModel
from typing import Optional, List
from datetime import date

# Voice Interaction Models
class VoiceQueryRequest(BaseModel):
    audio_base64: str
    session_id: Optional[str] = None
    language: Optional[str] = "hindi"

class VoiceResponse(BaseModel):
    text_response: str
    audio_base64: str
    language: str
    session_id: str
    user_text: Optional[str] = ""  # Add transcribed user text
    requires_camera: Optional[bool] = False  # Trigger camera for disease detection

class LanguageSelectionRequest(BaseModel):
    session_id: str
    language: str

# Farmer Profile Models
class FarmerProfile(BaseModel):
    farmer_id: Optional[int] = None
    name: str
    phone_number: str
    village: str
    district: str
    state: str
    land_size_acres: float
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None
    primary_crops: Optional[List[str]] = []

class FarmerProfileResponse(BaseModel):
    farmer_id: int
    name: str
    phone_number: str
    village: str
    district: str
    state: str
    land_size_acres: float
    soil_type: Optional[str]
    irrigation_type: Optional[str]
    primary_crops: Optional[List[str]]

# Crop & Land Models
class CropInformation(BaseModel):
    crop_id: Optional[int] = None
    farmer_id: int
    crop_name: str
    crop_variety: str
    sowing_date: date
    expected_harvest_date: Optional[date] = None
    land_area_acres: float
    current_stage: str  # germination, vegetative, flowering, harvest

class CropAdvisory(BaseModel):
    advisory_id: Optional[int] = None
    crop_id: int
    advisory_date: date
    advisory_type: str  # pest_control, fertilizer, irrigation, disease
    description: str
    severity: str  # low, medium, high, critical
    action_required: str

# Weather & Market Models
class WeatherInfo(BaseModel):
    location: str
    temperature: float
    humidity: float
    rainfall: float
    wind_speed: float
    weather_condition: str
    forecast_days: int

class MarketPrice(BaseModel):
    commodity: str
    market_name: str
    state: str
    district: str
    min_price: float
    max_price: float
    modal_price: float
    date: date

# Query Processing Models
class AgricultureQuery(BaseModel):
    query_text: str
    query_type: str  # crop_disease, weather, market_price, advisory, scheme
    language: str
    location: Optional[str] = None

class QueryResponse(BaseModel):
    response_text: str
    response_type: str
    data: Optional[dict] = None
    follow_up_questions: Optional[List[str]] = []

# Government Schemes
class GovernmentScheme(BaseModel):
    scheme_id: Optional[int] = None
    scheme_name: str
    scheme_name_hindi: str
    description: str
    description_hindi: str
    eligibility: str
    how_to_apply: str
    state: Optional[str] = None
    active: bool = True

# Pest & Disease Models
class PestDiseaseReport(BaseModel):
    report_id: Optional[int] = None
    farmer_id: int
    crop_id: int
    report_date: date
    symptoms: str
    image_url: Optional[str] = None
    identified_issue: Optional[str] = None
    recommended_treatment: Optional[str] = None
    severity: str

# Session Management
class SessionData(BaseModel):
    session_id: str
    farmer_id: Optional[int] = None
    language: str
    location: Optional[str] = None
    conversation_history: List[dict] = []
    last_activity: str