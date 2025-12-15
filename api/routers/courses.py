from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from api import schemas, crud, auth
from api.database import get_db

router = APIRouter(prefix="/api/courses", tags=["Courses"])


@router.get("/", response_model=List[schemas.CourseResponse])
def list_courses(
    level_id: Optional[int] = Query(None, description="Filter by level ID"),
    db: Session = Depends(get_db)
):
    """Get all courses, optionally filtered by level"""
    return crud.get_courses(db, level_id)


@router.post("/", response_model=schemas.CourseResponse, status_code=201)
def create_course(
    course: schemas.CourseCreate,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """Create a new course (requires authentication)"""
    try:
        return crud.create_course(db, course)
    except IntegrityError as e:
        db.rollback()
        if "UNIQUE constraint failed: courses.course_code" in str(e):
            raise HTTPException(status_code=400, detail=f"Course code '{course.course_code}' already exists")
        raise HTTPException(status_code=400, detail="Database constraint violation")


@router.get("/{course_id}", response_model=schemas.CourseResponse)
def get_course(course_id: int, db: Session = Depends(get_db)):
    """Get a specific course by ID"""
    course = crud.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.put("/{course_id}", response_model=schemas.CourseResponse)
def update_course(
    course_id: int,
    course: schemas.CourseCreate,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """Update a course (requires authentication)"""
    updated_course = crud.update_course(db, course_id, course)
    if not updated_course:
        raise HTTPException(status_code=404, detail="Course not found")
    return updated_course


@router.post("/{course_id}/assign-instructor", status_code=200)
def assign_instructor(
    course_id: int,
    request: schemas.AssignInstructorRequest,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """Assign an instructor to a course (requires authentication)"""
    if not crud.assign_instructor_to_course(db, course_id, request.instructor_id):
        raise HTTPException(status_code=404, detail="Course or Instructor not found")
    return {"message": "Instructor assigned successfully"}


@router.post("/{course_id}/assign-ta", status_code=200)
def assign_ta(
    course_id: int,
    request: schemas.AssignTARequest,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """Assign a TA to a course (requires authentication)"""
    if not crud.assign_ta_to_course(db, course_id, request.ta_id):
        raise HTTPException(status_code=404, detail="Course or TA not found")
    return {"message": "TA assigned successfully"}


@router.delete("/{course_id}", status_code=204)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """Delete a course (requires authentication)"""
    if not crud.delete_course(db, course_id):
        raise HTTPException(status_code=404, detail="Course not found")
