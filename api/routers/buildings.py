from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from api import schemas, crud, auth
from api.database import get_db

router = APIRouter(prefix="/api/buildings", tags=["Buildings"])


@router.get("/", response_model=List[schemas.BuildingResponse])
def list_buildings(db: Session = Depends(get_db)):
    """Get all buildings"""
    return crud.get_buildings(db)


@router.post("/", response_model=schemas.BuildingResponse, status_code=201)
def create_building(
    building: schemas.BuildingCreate,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """Create a new building (requires authentication)"""
    return crud.create_building(db, building)


@router.get("/{building_id}", response_model=schemas.BuildingResponse)
def get_building(building_id: int, db: Session = Depends(get_db)):
    """Get a specific building by ID"""
    building = crud.get_building(db, building_id)
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    return building


@router.put("/{building_id}", response_model=schemas.BuildingResponse)
def update_building(
    building_id: int,
    building: schemas.BuildingCreate,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """Update a building (requires authentication)"""
    updated_building = crud.update_building(db, building_id, building)
    if not updated_building:
        raise HTTPException(status_code=404, detail="Building not found")
    return updated_building


@router.delete("/{building_id}", status_code=204)
def delete_building(
    building_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """Delete a building (requires authentication)"""
    if not crud.delete_building(db, building_id):
        raise HTTPException(status_code=404, detail="Building not found")
