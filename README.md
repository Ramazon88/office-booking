# Office Room Booking System API

A FastAPI-based system for managing office room bookings.

## Features

- Office management (CRUD operations)
- Room management with capacity tracking
- Booking system with time conflict prevention
- JWT Authentication
- API Documentation (Swagger UI)
- Database migrations using Alembic
- Comprehensive test coverage

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with the following content:
```env
DATABASE_URL=sqlite:///./sql_app.db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

4. Initialize the database:
```bash
alembic upgrade head
```

5. Run the application:
```bash
uvicorn app.main:app --reload
```

## API Documentation

Once the application is running, you can access:
- Swagger UI documentation at: http://localhost:8000/docs
- ReDoc documentation at: http://localhost:8000/redoc

## Testing

Run tests using pytest:
```bash
pytest
```


