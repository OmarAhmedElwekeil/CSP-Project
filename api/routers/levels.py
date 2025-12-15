from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from api import schemas, crud, auth
from api.database import get_db

router = APIRouter(prefix="/api/levels", tags=["Levels"])


@router.get("/", response_model=List[schemas.LevelResponse])
def list_levels(db: Session = Depends(get_db)):
    """Get all levels"""
    return crud.get_levels(db)


@router.post("/", response_model=schemas.LevelResponse, status_code=201)
def create_level(
    level: schemas.LevelCreate,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """Create a new level with auto-generated sections and groups (requires authentication)"""
    return crud.create_level(db, level)


@router.get("/{level_id}", response_model=schemas.LevelResponse)
def get_level(level_id: int, db: Session = Depends(get_db)):
    """Get a specific level by ID"""
    level = crud.get_level(db, level_id)
    if not level:
        raise HTTPException(status_code=404, detail="Level not found")
    return level


@router.get("/{level_id}/sections", response_model=List[schemas.SectionResponse])
def get_level_sections(level_id: int, db: Session = Depends(get_db)):
    """Get all sections for a specific level"""
    level = crud.get_level(db, level_id)
    if not level:
        raise HTTPException(status_code=404, detail="Level not found")
    return crud.get_level_sections(db, level_id)


@router.get("/{level_id}/groups", response_model=List[schemas.GroupResponse])
def get_level_groups(level_id: int, db: Session = Depends(get_db)):
    """Get all groups for a specific level"""
    level = crud.get_level(db, level_id)
    if not level:
        raise HTTPException(status_code=404, detail="Level not found")
    return crud.get_level_groups(db, level_id)


@router.put("/{level_id}", response_model=schemas.LevelResponse)
def update_level(
    level_id: int,
    level: schemas.LevelCreate,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_admin_user)
):
    """Update a level (requires admin authentication)"""
    updated_level = crud.update_level(db, level_id, level)
    if not updated_level:
        raise HTTPException(status_code=404, detail="Level not found")
    return updated_level


@router.delete("/{level_id}", status_code=204)
def delete_level(
    level_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """Delete a level and all related sections/groups (requires authentication)"""
    if not crud.delete_level(db, level_id):
        raise HTTPException(status_code=404, detail="Level not found")
