"""Narrative service: template-based textual summary generation."""

from sqlalchemy.orm import Session


class NarrativeService:
    def __init__(self, db: Session):
        self.db = db

    def generate_narrative(self, city_id: int, city_name: str, scores: dict) -> str:
        """Generate a natural language narrative for a city's liveability."""
        overall = scores.get("overall_score", "N/A")
        climate = scores.get("climate_score", "N/A")
        affordability = scores.get("affordability_score", "N/A")
        safety = scores.get("safety_score", "N/A")
        environment = scores.get("environment_score", "N/A")

        return (
            f"{city_name} has an overall liveability score of {overall}/100. "
            f"Climate scores {climate}/100, "
            f"affordability {affordability}/100, "
            f"safety {safety}/100, "
            f"and environment {environment}/100."
        )
