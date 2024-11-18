from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.database import get_db
from app.models import Booking, Room, User
from app.schemas import BookingCreate, Booking as BookingSchema
from app.routers.auth import get_current_user
from datetime import datetime
from app.utils import end_time_must_be_after_start_time
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate

router = APIRouter()


def check_booking_conflict(db: Session, room_id: int, start_time: datetime, end_time: datetime,
                           booking_id: Optional[int] = None):
    query = db.query(Booking).filter(
        Booking.room_id == room_id,
        or_(
            and_(
                Booking.start_time <= start_time,
                Booking.end_time > start_time
            ),
            and_(
                Booking.start_time < end_time,
                Booking.end_time >= end_time
            ),
            and_(
                Booking.start_time >= start_time,
                Booking.end_time <= end_time
            )
        )
    )

    if booking_id:
        query = query.filter(Booking.id != booking_id)

    return query.first() is not None


@router.post("/bookings/", response_model=BookingSchema)
def create_booking(
        booking: BookingCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # Check if room exists
    room = db.query(Room).filter(Room.id == booking.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Check for booking conflicts
    if check_booking_conflict(db, booking.room_id, booking.start_time, booking.end_time):
        raise HTTPException(status_code=400, detail="Room is already booked for this time period")
    if end_time_must_be_after_start_time(start_time=booking.start_time, end_time=booking.end_time):
        raise HTTPException(status_code=400, detail="end_time must be after start_time")

    db_booking = Booking(**booking.dict(), user_id=current_user.id)
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking


def parse_datetime(value: str) -> datetime:
    try:
        return datetime.strptime(value, '%d-%m-%Y %H:%M')
    except ValueError:
        raise ValueError('Invalid datetime format. Please use DD-MM-YYYY HH:MM')

@router.get("/bookings/")
def read_bookings(
        user_id: Optional[int] = Query(None, description="Filter by user ID"),
        room_id: Optional[int] = Query(None, description="Filter by room ID"),
        start_time: Optional[str] = Query(None, description="Filter by start time DD-MM-YYYY HH:MM"),
        end_time: Optional[str] = Query(None, description="Filter by end time DD-MM-YYYY HH:MM"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
) -> Page[BookingSchema]:
    query = db.query(Booking)

    # Apply filters
    if room_id:
        query = query.filter(Booking.room_id == room_id)
    if user_id:
        query = query.filter(Booking.user_id == user_id)
    if start_time:
        start_time_parsed = parse_datetime(start_time)
        query = query.filter(Booking.start_time >= start_time_parsed)
    if end_time:
        end_time_parsed = parse_datetime(end_time)
        query = query.filter(Booking.end_time <= end_time_parsed)

    # Only show user's own bookings unless they're an admin
    query = query.filter(Booking.user_id == current_user.id)

    return paginate(query)


@router.get("/bookings/{booking_id}", response_model=BookingSchema)
def read_booking(
        booking_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this booking")
    return booking


@router.put("/bookings/{booking_id}", response_model=BookingSchema)
def update_booking(
        booking_id: int,
        booking: BookingCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    db_booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if db_booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    if db_booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this booking")

    # Check for booking conflicts
    if check_booking_conflict(db, booking.room_id, booking.start_time, booking.end_time, booking_id):
        raise HTTPException(status_code=400, detail="Room is already booked for this time period")

    for key, value in booking.dict().items():
        setattr(db_booking, key, value)

    db.commit()
    db.refresh(db_booking)
    return db_booking


@router.delete("/bookings/{booking_id}")
def delete_booking(
        booking_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    db_booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if db_booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    if db_booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this booking")

    db.delete(db_booking)
    db.commit()
    return {"message": "Booking deleted successfully"}
