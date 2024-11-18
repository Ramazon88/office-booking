from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Office, User
from app.schemas import OfficeCreate, Office as OfficeSchema
from app.routers.auth import get_current_user
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate

router = APIRouter()


@router.post("/offices/", response_model=OfficeSchema)
def create_office(
        office: OfficeCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    db_office = Office(**office.dict())
    db.add(db_office)
    db.commit()
    db.refresh(db_office)
    return db_office


@router.get("/offices/")
def read_offices(
        location: Optional[str] = Query(None, description="Filter by location"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
) -> Page[OfficeSchema]:
    query = db.query(Office)
    if location:
        query = query.filter(Office.location.ilike(f"%{location}%"))
    return paginate(query)


@router.get("/offices/{office_id}", response_model=OfficeSchema)
def read_office(
        office_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    db_office = db.query(Office).filter(Office.id == office_id).first()
    if db_office is None:
        raise HTTPException(status_code=404, detail="Office not found")
    return db_office


@router.put("/offices/{office_id}", response_model=OfficeSchema)
def update_office(
        office_id: int,
        office: OfficeCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    db_office = db.query(Office).filter(Office.id == office_id).first()
    if db_office is None:
        raise HTTPException(status_code=404, detail="Office not found")

    for key, value in office.dict().items():
        setattr(db_office, key, value)

    db.commit()
    db.refresh(db_office)
    return db_office


@router.delete("/offices/{office_id}")
def delete_office(
        office_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    db_office = db.query(Office).filter(Office.id == office_id).first()
    if db_office is None:
        raise HTTPException(status_code=404, detail="Office not found")

    db.delete(db_office)
    db.commit()
    return {"message": "Office deleted successfully"}
