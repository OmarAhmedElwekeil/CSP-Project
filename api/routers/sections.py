from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from api import schemas, crud, auth
from api.database import get_db

router = APIRouter(prefix="/api/sections", tags=["Sections"])


@router.get("/", response_model=List[schemas.SectionResponse])
def list_sections(db: Session = Depends(get_db)):
    """Get all sections"""
    return crud.get_sections(db)


@router.get("/{section_id}", response_model=schemas.SectionResponse)
def get_section(section_id: int, db: Session = Depends(get_db)):
    """Get a specific section by ID"""
    section = crud.get_section(db, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    return section


@router.delete("/{section_id}", status_code=204)
def delete_section(
    section_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """Delete a section and all related groups (requires authentication)"""
    if not crud.delete_section(db, section_id):
        raise HTTPException(status_code=404, detail="Section not found")
