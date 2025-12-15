from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from api import schemas, crud, auth
from api.database import get_db

router = APIRouter(prefix="/api/instructors", tags=["Instructors"])


@router.get("/", response_model=List[schemas.InstructorResponse])
def list_instructors(db: Session = Depends(get_db)):
    """Get all instructors"""
    return crud.get_instructors(db)


@router.post("/", response_model=schemas.InstructorResponse, status_code=201)
def create_instructor(
    instructor: schemas.InstructorCreate,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """Create a new instructor (requires authentication)"""
    try:
        return crud.create_instructor(db, instructor)
    except IntegrityError as e:
        db.rollback()
        if "UNIQUE constraint failed: instructors.instructor_name" in str(e):
            raise HTTPException(status_code=400, detail=f"Instructor name '{instructor.instructor_name}' already exists")
        raise HTTPException(status_code=400, detail="Database constraint violation")


@router.get("/{instructor_id}", response_model=schemas.InstructorResponse)
def get_instructor(instructor_id: int, db: Session = Depends(get_db)):
    """Get a specific instructor by ID"""
    instructor = crud.get_instructor(db, instructor_id)
    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found")
    return instructor


@router.put("/{instructor_id}", response_model=schemas.InstructorResponse)
def update_instructor(
    instructor_id: int,
    instructor: schemas.InstructorCreate,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """Update an instructor (requires authentication)"""
    updated_instructor = crud.update_instructor(db, instructor_id, instructor)
    if not updated_instructor:
        raise HTTPException(status_code=404, detail="Instructor not found")
    return updated_instructor


@router.get("/{instructor_id}/courses", response_model=List[schemas.CourseResponse])
def get_instructor_courses(instructor_id: int, db: Session = Depends(get_db)):
    """Get all courses assigned to an instructor"""
    instructor = crud.get_instructor(db, instructor_id)
    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found")
    return crud.get_instructor_courses(db, instructor_id)


@router.post("/{instructor_id}/courses/{course_id}", status_code=201)
def assign_course_to_instructor(
    instructor_id: int,
    course_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """Assign a course to an instructor (requires authentication)"""
    if not crud.assign_instructor_to_course(db, course_id, instructor_id):
        raise HTTPException(status_code=404, detail="Instructor or course not found")
    return {"message": "Course assigned successfully"}


@router.delete("/{instructor_id}/courses/{course_id}", status_code=204)
def remove_course_from_instructor(
    instructor_id: int,
    course_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """Remove a course from an instructor (requires authentication)"""
    instructor = crud.get_instructor(db, instructor_id)
    course = crud.get_course(db, course_id)
    
    if not instructor or not course:
        raise HTTPException(status_code=404, detail="Instructor or course not found")
    
    if course in instructor.courses:
        instructor.courses.remove(course)
        db.commit()


@router.delete("/{instructor_id}", status_code=204)
def delete_instructor(
    instructor_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """Delete an instructor (requires authentication)"""
    if not crud.delete_instructor(db, instructor_id):
        raise HTTPException(status_code=404, detail="Instructor not found")
