from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator


# Office schemas
class OfficeBase(BaseModel):
    name: str
    location: str


class OfficeCreate(OfficeBase):
    pass


class Office(OfficeBase):
    id: int

    class Config:
        from_attributes = True


# Room schemas
class RoomBase(BaseModel):
    name: str
    capacity: Optional[int] = None


class RoomCreate(RoomBase):
    office_id: int


class Room(RoomBase):
    id: int
    office_id: int

    class Config:
        from_attributes = True


# User schemas
class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int

    class Config:
        from_attributes = True


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[int] = None


# Booking schemas
class BookingBase(BaseModel):
    start_time: datetime
    end_time: datetime

    @field_validator('start_time', 'end_time', mode='before')
    @classmethod
    def parse_datetime(cls, value):
        if isinstance(value, str):
            try:
                return datetime.strptime(value, '%d-%m-%Y %H:%M')
            except ValueError:
                raise ValueError('Invalid datetime format. Please use DD-MM-YYYY HH:MM')

        return value

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime('%d-%m-%Y %H:%M')
        }
        schema_extra = {
            "example": {
                "start_time": "19-10-2024 10:00",
                "end_time": "19-11-2024 12:00"
            }
        }


class BookingCreate(BookingBase):
    room_id: int

    class Config:
        schema_extra = {
            "example": {
                "start_time": "19-10-2024 10:00",
                "end_time": "19-11-2024 12:00"
            }
        }


class Booking(BookingBase):
    id: int
    room_id: int
    user_id: int

    class Config:
        from_attributes = True

