from datetime import date
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

Interest = Literal["nature", "food", "cafe", "culture", "shopping", "beach"]

class UserSurvey(BaseModel):
    style: Literal["nature", "city"]
    place: Literal["indoor", "outdoor"]
    activity: Literal["active", "relax"]
    interests: List[Interest] = Field(default_factory=list)
    start_lat: float = Field(..., ge=32.8, le=34.1)
    start_lng: float = Field(..., ge=125.8, le=127.2)
    travel_date: date
    days: int = Field(1, ge=1, le=5)
    start_time: str = Field("09:00", pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    end_time: str = Field("19:00", pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    weather_tolerance: Literal["any", "indoor"] = "any"
    top_n: int = Field(5, ge=3, le=10)

class PlaceInfo(BaseModel):
    name: str; vector: List[float]; coordinates: List[float]; score: float
    category: str = ""; address: str = ""; overview: str = ""
    place_type: str = "attraction"; estimated_duration_minutes: int = 90
    arrival_time: Optional[str] = None; departure_time: Optional[str] = None
    travel_minutes_from_previous: Optional[int] = None
    map_search_url: str = ""; booking_search_url: str = ""

class TravelPlan(BaseModel):
    id: Literal["preference", "weather", "nearby"]
    title: str; subtitle: str; reason: str; total_distance: float; total_minutes: int
    places: List[PlaceInfo]

class RecommendResponse(BaseModel):
    plans: List[TravelPlan]
    weather: dict
    message: str
