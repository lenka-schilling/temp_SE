import motor.motor_asyncio
from beanie import init_beanie
from app.models.measurements import Measurement
from app.models.forecasts import Forecast
from app.models.core import User, Building, Room

async def init_db(uri: str):
    client = motor.motor_asyncio.AsyncIOMotorClient(uri)

    await init_beanie(database=client.Measurements, document_models=[
        Measurement, Forecast, User, Building, Room
    ])