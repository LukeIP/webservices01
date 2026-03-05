"""Natural language query schemas."""

from pydantic import BaseModel, Field



class NarrativeResponse(BaseModel):
    city_id: int
    city_name: str
    narrative: str
