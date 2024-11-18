from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Room, User, Office
from app.schemas import RoomCreate, Room as RoomSchema
from app.routers.auth import get_current_user
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate

router = APIRouter()


@router.post("/rooms/", response_model=RoomSchema)
def create_room(
        room: RoomCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    office_exists = db.query(Office).filter(Office.id == room.office_id).first()
    if not office_exists:
        raise HTTPException(status_code=400, detail="Invalid office_id")
    db_room = Room(**room.dict())
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room


@router.get("/rooms/")
def read_rooms(
        office_id: Optional[int] = Query(None, description="Filter by office ID"),
        capacity: Optional[int] = Query(None, description="Filter by capacity"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
) -> Page[RoomSchema]:
    query = db.query(Room)
    if office_id:
        query = query.filter(Room.office_id == office_id)
    if capacity:
        query = query.filter(Room.capacity == capacity)
    return paginate(query)


@router.get("/rooms/{room_id}", response_model=RoomSchema)
def read_room(
        room_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    db_room = db.query(Room).filter(Room.id == room_id).first()
    if db_room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return db_room


@router.put("/rooms/{room_id}", response_model=RoomSchema)
def update_room(
        room_id: int,
        room: RoomCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    office_exists = db.query(Office).filter(Office.id == room.office_id).first()
    if not office_exists:
        raise HTTPException(status_code=400, detail="Invalid office_id")
    db_room = db.query(Room).filter(Room.id == room_id).first()
    if db_room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    for key, value in room.dict().items():
        setattr(db_room, key, value)

    db.commit()
    db.refresh(db_room)
    return db_room


@router.delete("/rooms/{room_id}")
def delete_room(
        room_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    db_room = db.query(Room).filter(Room.id == room_id).first()
    if db_room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    db.delete(db_room)
    db.commit()
    return {"message": "Room deleted successfully"}
