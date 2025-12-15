from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from api import schemas, crud, auth
from api.database import get_db

router = APIRouter(prefix="/api/groups", tags=["Groups"])


@router.get("/", response_model=List[schemas.GroupResponse])
def list_groups(db: Session = Depends(get_db)):
    """Get all groups"""
    return crud.get_groups(db)


@router.get("/{group_id}", response_model=schemas.GroupResponse)
def get_group(group_id: int, db: Session = Depends(get_db)):
    """Get a specific group by ID"""
    group = crud.get_group(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@router.get("/{group_id}/sections", response_model=List[schemas.SectionResponse])
def get_group_sections(group_id: int, db: Session = Depends(get_db)):
    """Get all sections belonging to a specific group"""
    return crud.get_group_sections(db, group_id)


@router.delete("/{group_id}", status_code=204)
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """Delete a group (requires authentication)"""
    if not crud.delete_group(db, group_id):
        raise HTTPException(status_code=404, detail="Group not found")
