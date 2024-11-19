import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import datetime as base_datetime
from app.main import app
from app.database import Base, get_db
from app.models import User, Office, Room, Booking
from app.utils import get_password_hash

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(test_db):
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_office(test_db):
    office = Office(name="Test Office", location="Test Location")
    test_db.add(office)
    test_db.commit()
    test_db.refresh(office)
    return office


@pytest.fixture
def test_room(test_db, test_office):
    room = Room(name="Test Room", capacity=10, office_id=test_office.id)
    test_db.add(room)
    test_db.commit()
    test_db.refresh(room)
    return room


@pytest.fixture
def access_token(client, test_user):
    response = client.post(
        "/token",
        data={"username": "test@example.com", "password": "testpassword"}
    )
    return response.json()["access_token"]


def test_create_booking(client, test_room, access_token):
    start_time = datetime.now(base_datetime.UTC) + timedelta(hours=1)
    end_time = start_time + timedelta(hours=1)

    response = client.post(
        "/bookings/",
        json={
            "room_id": test_room.id,
            "start_time": start_time.strftime('%d-%m-%Y %H:%M'),
            "end_time": end_time.strftime('%d-%m-%Y %H:%M')
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["room_id"] == test_room.id


def test_booking_conflict(client, test_room, test_db, test_user, access_token):
    # Create initial booking
    start_time = datetime.now(base_datetime.UTC) + timedelta(hours=1)
    end_time = start_time + timedelta(hours=1)

    booking = Booking(
        room_id=test_room.id,
        user_id=test_user.id,
        start_time=start_time,
        end_time=end_time
    )
    test_db.add(booking)
    test_db.commit()

    # Try to create overlapping booking
    response = client.post(
        "/bookings/",
        json={
            "room_id": test_room.id,
            "start_time": start_time.strftime('%d-%m-%Y %H:%M'),
            "end_time": end_time.strftime('%d-%m-%Y %H:%M')
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 400
    assert "already booked" in response.json()["detail"]


def test_delete_booking(client, test_db, test_room, test_user, access_token):
    # Create a booking
    booking = Booking(
        room_id=test_room.id,
        user_id=test_user.id,
        start_time=datetime.now(base_datetime.UTC) + timedelta(hours=1),
        end_time=datetime.now(base_datetime.UTC) + timedelta(hours=2)
    )
    test_db.add(booking)
    test_db.commit()

    response = client.delete(
        f"/bookings/{booking.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Booking deleted successfully"
