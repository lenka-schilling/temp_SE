from typing import List, Optional, Dict, Any
from datetime import datetime
from app.schemas.dac_interfaces import (
    IMeasurement, IForecastRead, IForecastWrite, ICoreDb,
    Measurement as MeasurementSchema, 
    ForecastData, BuildingMetadata, DeviceMetadata, UserSchema
)
from app.models.measurements import Measurement as MeasurementModel
from app.models.forecasts import Forecast as ForecastModel

class DataAccessGateway(IMeasurement, IForecastRead, IForecastWrite, ICoreDb):
    
    # =========================================================
    # 1. MEASUREMENTS (Functional - Connects to MongoDB)
    # =========================================================
    async def get_measurements(
        self, building_id: str, metric_type: str, 
        start_date: datetime, end_date: datetime, 
        device_ids: Optional[List[str]] = None
    ) -> List[MeasurementSchema]:
        
        query = {
            "metric": metric_type,
            "ts": {"$gte": start_date, "$lte": end_date}
        }
        if device_ids:
            query["deviceId"] = {"$in": device_ids}
            
        results = await MeasurementModel.find(query).sort("ts").to_list()
        
        return [
            MeasurementSchema(
                id=str(r.id),
                device_id=r.deviceId,
                metric=r.metric,
                value=r.value,
                timestamp=r.ts,
                tags=r.tags
            ) for r in results
        ]

    async def get_aggregated_measurements(self, *args, **kwargs):
        return []

    # =========================================================
    # 2. FORECASTS (Functional - Connects to MongoDB)
    # =========================================================
    async def create_forecast(
        self, forecast_type: str, horizon: str, building_id: str,
        requested_by: str, series_data: List[Dict[str, Any]],
        valid_from: datetime, valid_to: datetime,
        model_algorithm: str, model_version: str,
        room_id: Optional[str] = None, floor_id: Optional[str] = None
    ) -> str:
        
        # We can implement this because 'Forecasts' collection exists in Mongo
        #
        scope = {"buildingId": building_id}
        if room_id: scope["roomId"] = room_id
        if floor_id: scope["floorId"] = floor_id

        new_forecast = ForecastModel(
            type=forecast_type,
            horizon=horizon,
            issued_at=datetime.utcnow(),
            requested_by=requested_by,
            series_item=series_data,
            valid_for={"from": valid_from, "to": valid_to},
            model_meta={"algo": model_algorithm, "ver": model_version},
            scope=scope
        )
        await new_forecast.insert()
        return str(new_forecast.id)

    async def update_forecast(self, forecast_id: str, series_data: List[Dict]):
        f = await ForecastModel.get(forecast_id)
        if f:
            f.series_item = series_data
            await f.save()
            return True
        return False

    async def get_latest_forecast(self, building_id: str, forecast_type: str, horizon: str) -> Optional[ForecastData]:
        f = await ForecastModel.find(
            {"scope.buildingId": building_id, "type": forecast_type, "horizon": horizon}
        ).sort("-issued_at").first_or_none()
        return self._map_to_schema(f) if f else None

    async def get_forecast_by_id(self, forecast_id: str) -> Optional[ForecastData]:
        f = await ForecastModel.get(forecast_id)
        return self._map_to_schema(f) if f else None

    async def get_forecasts_in_range(self, *args, **kwargs):
        return []

    def _map_to_schema(self, f: ForecastModel) -> ForecastData:
        return ForecastData(
            id=str(f.id),
            type=f.type,
            horizon=f.horizon,
            issued_at=f.issued_at,
            requested_by=f.requested_by,
            series_item=f.series_item,
            valid_for=f.valid_for,
            model_meta=f.model_meta,
            scope=f.scope
        )

    # =========================================================
    # 3. CORE DB (Non-Functional Interface / Stubs)
    # =========================================================
    # The optimization team says CoreDb is PostgreSQL.
    # Since we are not responsible for creating it and don't have access,
    # we implement the interface to return None/Empty.
    
    async def get_building(self, building_id: str) -> Optional[BuildingMetadata]:
        # TODO: Connect to PostgreSQL when DB Team provides credentials.
        return None 

    async def get_devices(self, building_id: str, device_type: Optional[str] = None, status: Optional[str] = "active") -> List[DeviceMetadata]:
        # TODO: Connect to PostgreSQL when DB Team provides credentials.
        return []

    async def get_device(self, device_id: str) -> Optional[DeviceMetadata]:
        # TODO: Connect to PostgreSQL when DB Team provides credentials.
        return None
        
    async def get_user_by_username(self, username: str) -> Optional[UserSchema]:
         # TODO: Connect to PostgreSQL when DB Team provides credentials.
        return None