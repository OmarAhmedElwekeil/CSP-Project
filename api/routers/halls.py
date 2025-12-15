from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from api import schemas, crud, auth
from api.database import get_db

router = APIRouter(prefix="/api/halls", tags=["Halls"])


@router.get("/", response_model=List[schemas.HallResponse])
def list_halls(db: Session = Depends(get_db)):
    """Get all halls"""
    return crud.get_halls(db)


@router.post("/", response_model=schemas.HallResponse, status_code=201)
def create_hall(
    hall: schemas.HallCreate,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """Create a new hall (requires authentication)"""
    return crud.create_hall(db, hall)


@router.get("/{hall_id}", response_model=schemas.HallResponse)
def get_hall(hall_id: int, db: Session = Depends(get_db)):
    """Get a specific hall by ID"""
    hall = crud.get_hall(db, hall_id)
    if not hall:
        raise HTTPException(status_code=404, detail="Hall not found")
    return hall


@router.put("/{hall_id}", response_model=schemas.HallResponse)
def update_hall(
    hall_id: int,
    hall: schemas.HallCreate,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """Update a hall (requires authentication)"""
    updated_hall = crud.update_hall(db, hall_id, hall)
    if not updated_hall:
        raise HTTPException(status_code=404, detail="Hall not found")
    return updated_hall


@router.delete("/{hall_id}", status_code=204)
def delete_hall(
    hall_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """Delete a hall (requires authentication)"""
    if not crud.delete_hall(db, hall_id):
        raise HTTPException(status_code=404, detail="Hall not found")
