"""Analytics service — liveability scoring, trends, anomaly detection."""

from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import math

from app.models.city import City
from app.models.climate_metric import ClimateMetric
from app.models.socioeconomic_metric import SocioeconomicMetric
from app.models.liveability_score import LiveabilityScore
from app.models.rent_submission import RentSubmission
from app.utils.scoring import compute_liveability
from app.exceptions import NotFoundException


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def _get_city_or_404(self, city_id: int) -> City:
        city = self.db.query(City).filter(City.id == city_id).first()
        if not city:
            raise NotFoundException("City", city_id)
        return city

    def compute_liveability_for_city(self, city_id: int) -> dict:
        """Compute and store liveability score for a city."""
        city = self._get_city_or_404(city_id)

        # Get latest climate metrics (average of last 30 days)
        climate = (
            self.db.query(
                func.avg(ClimateMetric.avg_temp_c).label("avg_temp"),
                func.avg(ClimateMetric.aqi).label("avg_aqi"),
            )
            .filter(ClimateMetric.city_id == city_id)
            .first()
        )

        # Get latest socioeconomic metrics
        socio = (
            self.db.query(SocioeconomicMetric)
            .filter(SocioeconomicMetric.city_id == city_id)
            .order_by(SocioeconomicMetric.year.desc())
            .first()
        )

        # Prefer crowdsourced median rent for the current year; fall back to seed data
        current_year = date.today().year
        rent_values = [
            r[0] for r in self.db.query(RentSubmission.rent_amount_gbp)
            .filter(RentSubmission.city_id == city_id, RentSubmission.year == current_year)
            .all()
        ]
        if rent_values:
            s = sorted(rent_values)
            n = len(s)
            median_rent = s[n // 2] if n % 2 == 1 else (s[n // 2 - 1] + s[n // 2]) / 2
        else:
            median_rent = socio.median_rent_gbp if socio else None

        scores = compute_liveability(
            avg_temp=climate.avg_temp if climate else None,
            aqi=climate.avg_aqi if climate else None,
            median_rent=median_rent,
            crime_index=socio.crime_index if socio else None,
            green_space_pct=socio.green_space_pct if socio else None,
        )

        # Store the score
        ls = LiveabilityScore(
            city_id=city_id,
            overall_score=scores["overall_score"],
            climate_score=scores["climate_score"],
            affordability_score=scores["affordability_score"],
            safety_score=scores["safety_score"],
            environment_score=scores["environment_score"],
            weights_used=scores["weights_used"],
        )
        self.db.add(ls)
        self.db.commit()

        return {
            "city_id": city_id,
            "city_name": city.name,
            **scores,
        }

    def compare_cities(self, city_ids: list[int]) -> list[dict]:
        """Compute liveability for multiple cities and return comparison."""
        results = []
        for cid in city_ids:
            try:
                result = self.compute_liveability_for_city(cid)
                results.append(result)
            except NotFoundException:
                continue
        return results

    def get_trends(self, city_id: int, metric: str = "aqi", period: str = "12m") -> dict:
        """Get time-series trend data for a metric."""
        city = self._get_city_or_404(city_id)

        # Parse period
        months = int(period.replace("m", "")) if period.endswith("m") else 12
        start_date = date.today() - timedelta(days=months * 30)

        # Map metric to column
        metric_map = {
            "aqi": ClimateMetric.aqi,
            "temp": ClimateMetric.avg_temp_c,
            "humidity": ClimateMetric.humidity_pct,
            "precipitation": ClimateMetric.precipitation_mm,
        }

        col = metric_map.get(metric)
        if col is None:
            from app.exceptions import AppException
            raise AppException(detail=f"Invalid metric '{metric}'. Valid: {list(metric_map.keys())}", status_code=400, code="INVALID_METRIC")

        rows = (
            self.db.query(ClimateMetric.date, col)
            .filter(ClimateMetric.city_id == city_id, ClimateMetric.date >= start_date)
            .order_by(ClimateMetric.date.asc())
            .all()
        )

        data_points = [
            {"date": row[0].isoformat(), "value": float(row[1]) if row[1] is not None else 0.0}
            for row in rows
        ]

        return {
            "city_id": city_id,
            "metric": metric,
            "period": period,
            "data_points": data_points,
        }

    def detect_anomalies(self, city_id: int, threshold: float = 2.0) -> dict:
        """Detect anomalous metric readings using z-score method."""
        city = self._get_city_or_404(city_id)

        metrics = (
            self.db.query(ClimateMetric)
            .filter(ClimateMetric.city_id == city_id)
            .order_by(ClimateMetric.date.asc())
            .all()
        )

        if not metrics:
            return {"city_id": city_id, "anomalies": [], "threshold": threshold}

        anomalies = []

        for field_name in ["aqi", "avg_temp_c", "humidity_pct", "precipitation_mm"]:
            values = [getattr(m, field_name) for m in metrics if getattr(m, field_name) is not None]
            if len(values) < 3:
                continue

            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            std = math.sqrt(variance) if variance > 0 else 1.0

            for m in metrics:
                val = getattr(m, field_name)
                if val is None:
                    continue
                z = (val - mean) / std
                if abs(z) >= threshold:
                    anomalies.append({
                        "date": m.date.isoformat(),
                        "metric": field_name,
                        "value": float(val),
                        "z_score": round(z, 3),
                        "is_anomaly": True,
                    })

        return {"city_id": city_id, "anomalies": anomalies, "threshold": threshold}
