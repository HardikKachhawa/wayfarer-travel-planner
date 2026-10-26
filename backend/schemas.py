from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, model_validator


class TripRequest(BaseModel):
    destination: str = Field(min_length=2)
    start_date: date
    end_date: date
    budget: float = Field(gt=0)
    currency: str = "INR"
    travelers: int = Field(default=1, ge=1, le=20)
    interests: list[str] = []
    pace: Literal["relaxed", "balanced", "packed"] = "balanced"
    stay: Literal["budget", "comfort", "premium"] = "comfort"
    notes: str = ""

    @model_validator(mode="after")
    def check_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        if (self.end_date - self.start_date).days >= 14:
            raise ValueError("Trips are limited to 14 days")
        return self

    @property
    def days(self) -> int:
        return (self.end_date - self.start_date).days + 1


class Activity(BaseModel):
    time: str = "09:00"
    name: str
    type: str = "sightseeing"  # sightseeing | food | stay | transport | activity
    duration_min: int = 60
    cost: float = 0
    notes: str = ""


class Day(BaseModel):
    day: int
    theme: str = ""
    activities: list[Activity] = []


class Itinerary(BaseModel):
    summary: str = ""
    stay_suggestion: str = ""
    transport_tips: str = ""
    days: list[Day]


class RegenerateDay(BaseModel):
    request: TripRequest
    itinerary: Itinerary
    day: int
    instruction: str = ""


class TripIn(BaseModel):
    title: str
    request: TripRequest
    itinerary: Itinerary
