from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from api import schemas, crud, auth
from api.database import get_db

router = APIRouter(prefix="/api/tas", tags=["TAs"])


@router.get("/", response_model=List[schemas.TAResponse])
def list_tas(db: Session = Depends(get_db)):
    """Get all TAs"""
    return crud.get_tas(db)


@router.post("/", response_model=schemas.TAResponse, status_code=201)
def create_ta(
    ta: schemas.TACreate,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """Create a new TA (requires authentication)"""
    try:
        return crud.create_ta(db, ta)
    except IntegrityError as e:
        db.rollback()
        if "UNIQUE constraint failed: tas.ta_name" in str(e):
            raise HTTPException(status_code=400, detail=f"TA name '{ta.ta_name}' already exists")
        raise HTTPException(status_code=400, detail="Database constraint violation")


@router.get("/{ta_id}", response_model=schemas.TAResponse)
def get_ta(ta_id: int, db: Session = Depends(get_db)):
    """Get a specific TA by ID"""
    ta = crud.get_ta(db, ta_id)
    if not ta:
        raise HTTPException(status_code=404, detail="TA not found")
    return ta


@router.put("/{ta_id}", response_model=schemas.TAResponse)
def update_ta(
    ta_id: int,
    ta: schemas.TACreate,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """Update a TA (requires authentication)"""
    updated_ta = crud.update_ta(db, ta_id, ta)
    if not updated_ta:
        raise HTTPException(status_code=404, detail="TA not found")
    return updated_ta


@router.get("/{ta_id}/courses", response_model=List[schemas.CourseResponse])
def get_ta_courses(ta_id: int, db: Session = Depends(get_db)):
    """Get all courses assigned to a TA"""
    ta = crud.get_ta(db, ta_id)
    if not ta:
        raise HTTPException(status_code=404, detail="TA not found")
    return crud.get_ta_courses(db, ta_id)


@router.post("/{ta_id}/courses/{course_id}", status_code=201)
def assign_course_to_ta(
    ta_id: int,
    course_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """Assign a course to a TA (requires authentication)"""
    if not crud.assign_ta_to_course(db, course_id, ta_id):
        raise HTTPException(status_code=404, detail="TA or course not found")
    return {"message": "Course assigned successfully"}


@router.delete("/{ta_id}/courses/{course_id}", status_code=204)
def remove_course_from_ta(
    ta_id: int,
    course_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """Remove a course from a TA (requires authentication)"""
    ta = crud.get_ta(db, ta_id)
    course = crud.get_course(db, course_id)
    
    if not ta or not course:
        raise HTTPException(status_code=404, detail="TA or course not found")
    
    if course in ta.courses:
        ta.courses.remove(course)
        db.commit()


@router.delete("/{ta_id}", status_code=204)
def delete_ta(
    ta_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """Delete a TA (requires authentication)"""
    if not crud.delete_ta(db, ta_id):
        raise HTTPException(status_code=404, detail="TA not found")
