"""Metric service — CRUD for climate and socioeconomic metrics."""

from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.city import City
from app.models.climate_metric import ClimateMetric
from app.models.socioeconomic_metric import SocioeconomicMetric
from app.schemas.metric import ClimateMetricCreate, SocioeconomicMetricCreate
from app.exceptions import NotFoundException


class MetricService:
    def __init__(self, db: Session):
        self.db = db

    def _get_city_or_404(self, city_id: int) -> City:
        city = self.db.query(City).filter(City.id == city_id).first()
        if not city:
            raise NotFoundException("City", city_id)
        return city

    # ---- Climate Metrics ----

    def create_climate_metric(self, city_id: int, data: ClimateMetricCreate) -> ClimateMetric:
        self._get_city_or_404(city_id)
        metric = ClimateMetric(city_id=city_id, **data.model_dump())
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        return metric

    def list_climate_metrics(
        self,
        city_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[ClimateMetric], int]:
        self._get_city_or_404(city_id)
        query = self.db.query(ClimateMetric).filter(ClimateMetric.city_id == city_id)
        if start_date:
            query = query.filter(ClimateMetric.date >= start_date)
        if end_date:
            query = query.filter(ClimateMetric.date <= end_date)
        total = query.count()
        items = query.order_by(ClimateMetric.date.desc()).offset(offset).limit(limit).all()
        return items, total

    def get_climate_metric(self, metric_id: int) -> ClimateMetric:
        metric = self.db.query(ClimateMetric).filter(ClimateMetric.id == metric_id).first()
        if not metric:
            raise NotFoundException("ClimateMetric", metric_id)
        return metric

    def delete_climate_metric(self, metric_id: int) -> None:
        metric = self.get_climate_metric(metric_id)
        self.db.delete(metric)
        self.db.commit()

    # ---- Socioeconomic Metrics ----

    def create_socioeconomic_metric(self, city_id: int, data: SocioeconomicMetricCreate) -> SocioeconomicMetric:
        self._get_city_or_404(city_id)
        metric = SocioeconomicMetric(city_id=city_id, **data.model_dump())
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        return metric

    def list_socioeconomic_metrics(
        self,
        city_id: int,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[SocioeconomicMetric], int]:
        self._get_city_or_404(city_id)
        query = self.db.query(SocioeconomicMetric).filter(SocioeconomicMetric.city_id == city_id)
        total = query.count()
        items = query.order_by(SocioeconomicMetric.year.desc()).offset(offset).limit(limit).all()
        return items, total

    def get_socioeconomic_metric(self, metric_id: int) -> SocioeconomicMetric:
        metric = self.db.query(SocioeconomicMetric).filter(SocioeconomicMetric.id == metric_id).first()
        if not metric:
            raise NotFoundException("SocioeconomicMetric", metric_id)
        return metric

    def delete_socioeconomic_metric(self, metric_id: int) -> None:
        metric = self.get_socioeconomic_metric(metric_id)
        self.db.delete(metric)
        self.db.commit()
