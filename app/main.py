import logging
import os
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI
from fastapi_pagination import add_pagination

from app.database import engine, Base
from app.routers import auth, office, room, booking

# Configure logging
if not os.path.exists("logs"):
    os.makedirs("logs")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            "logs/app.log",
            maxBytes=10000000,  # 10MB
            backupCount=5
        ),
        logging.StreamHandler()
    ]
)

# Create logger
logger = logging.getLogger("office_booking")
Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="Office Booking Service",
)
add_pagination(app)
app.include_router(auth.router, tags=["authentication"])
app.include_router(office.router, tags=["offices"])
app.include_router(room.router, tags=["rooms"])
app.include_router(booking.router, tags=["booking"])


@app.get("/")
def root():
    return {"message": "Welcome to the Office Room Booking System API"}
