from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd
from io import BytesIO
from api import schemas, crud, auth, models
from api.database import get_db
from api.scheduler import CSPScheduler

router = APIRouter(prefix="/api/schedule", tags=["Schedule"])


@router.get("/", response_model=List[schemas.ScheduleDetailResponse])
def get_schedule(
    day: Optional[str] = Query(None, description="Filter by day"),
    instructor_id: Optional[int] = Query(None, description="Filter by instructor ID"),
    ta_id: Optional[int] = Query(None, description="Filter by TA ID"),
    course_id: Optional[int] = Query(None, description="Filter by course ID"),
    group_id: Optional[int] = Query(None, description="Filter by group ID"),
    room_id: Optional[int] = Query(None, description="Filter by room ID"),
    level_id: Optional[int] = Query(None, description="Filter by level ID"),
    db: Session = Depends(get_db)
):
    """
    Get schedule entries with optional filters.
    Returns detailed schedule information with block system data.
    """
    query = db.query(models.Schedule)
    
    # Apply filters
    if instructor_id:
        query = query.filter(models.Schedule.instructor_id == instructor_id)
    if ta_id:
        query = query.filter(models.Schedule.ta_id == ta_id)
    if course_id:
        query = query.filter(models.Schedule.course_id == course_id)
    if group_id:
        query = query.filter(models.Schedule.group_id == group_id)
    if room_id:
        query = query.filter(models.Schedule.room_id == room_id)
    
    schedule_entries = query.all()
    
    # Apply day filter after loading (since day is in timeslot)
    if day:
        schedule_entries = [entry for entry in schedule_entries if entry.timeslot.day == day]
    
    # Transform to detailed response with block info
    detailed_schedule = []
    for entry in schedule_entries:
        instructor_or_ta = entry.instructor.instructor_name if entry.instructor else (
            entry.ta.ta_name if entry.ta else "N/A"
        )
        
        # Get timeslot data
        timeslot = entry.timeslot
        
        # Calculate duration in minutes
        start_parts = timeslot.start_time.split(':')
        end_parts = timeslot.end_time.split(':')
        start_mins = int(start_parts[0]) * 60 + int(start_parts[1])
        end_mins = int(end_parts[0]) * 60 + int(end_parts[1])
        duration_mins = end_mins - start_mins
        duration_blocks = 2 if duration_mins == 90 else 1
        
        # Calculate start_block from start_time
        # Block schedule: 9:00 (block 0), 9:45 (1), 10:45 (2), 11:30 (3), 12:30 (4), 13:15 (5), 14:15 (6), 15:00 (7)
        time_to_block = {
            "09:00": 0, "09:45": 1, "10:45": 2, "11:30": 3,
            "12:30": 4, "13:15": 5, "14:15": 6, "15:00": 7
        }
        start_block = time_to_block.get(timeslot.start_time[:5], 0)
        
        # Get level info from group
        level_name = entry.group.level.level_name
        level_id = entry.group.level.level_id
        group_number = entry.group.group_number
        
        # Get section number from the section relationship (None for lectures)
        section_number = entry.section.section_number if entry.section else None
        
        detailed_schedule.append(schemas.ScheduleDetailResponse(
            day=timeslot.day,
            start_time=timeslot.start_time[:5],  # Remove seconds
            end_time=timeslot.end_time[:5],
            start_block=start_block,
            duration_blocks=duration_blocks,
            course_code=entry.course.course_code,
            course_name=entry.course.course_name,
            instructor_or_ta=instructor_or_ta,
            room_number=entry.room.room_number,
            building_name=entry.room.building.building_name,
            level_name=level_name,
            level_id=level_id,
            section_number=section_number,
            group_number=group_number,
            session_type=entry.session_type
        ))
    
    return detailed_schedule


@router.post("/generate", status_code=200)
def generate_schedule(
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_admin_user)
):
    """
    Generate the complete schedule using the CSP algorithm.
    Requires admin privileges.
    """
    try:
        scheduler = CSPScheduler(db)
        result = scheduler.generate_schedule()
        
        return {
            "success": True,
            "message": f"Schedule generated successfully with {len(result)} sessions",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/", status_code=200)
def clear_schedule(
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_admin_user)
):
    """
    Clear all schedule entries.
    Requires admin privileges.
    """
    crud.clear_schedule(db)
    return {"message": "Schedule cleared successfully"}


@router.get("/export")
def export_schedule(db: Session = Depends(get_db)):
    """
    Export the schedule to an Excel file.
    Returns the file as a download.
    """
    # Get all schedule entries
    schedule_entries = db.query(models.Schedule).all()
    
    if not schedule_entries:
        raise HTTPException(status_code=404, detail="No schedule data to export")
    
    # Prepare data for DataFrame
    data = []
    for entry in schedule_entries:
        instructor_or_ta = entry.instructor.instructor_name if entry.instructor else (
            entry.ta.ta_name if entry.ta else "N/A"
        )
        
        # Get section number (first section if multiple exist)
        section_number = entry.group.sections[0].section_number if entry.group.sections else 0
        
        data.append({
            "Day": entry.timeslot.day,
            "Start Time": entry.timeslot.start_time,
            "End Time": entry.timeslot.end_time,
            "Course Code": entry.course.course_code,
            "Course Name": entry.course.course_name,
            "Instructor/TA": instructor_or_ta,
            "Room": entry.room.room_number,
            "Building": entry.room.building.building_name,
            "Level": entry.group.level.level_name,
            "Section": section_number,
            "Group": entry.group.group_number,
            "Duration": entry.timeslot.duration,
            "Session Type": entry.session_type
        })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Schedule', index=False)
    
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=schedule.xlsx"}
    )


@router.post("/import", status_code=200)
async def import_data(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_admin_user)
):
    """
    Import data from an Excel file.
    Expected sheets: Courses, Instructors, TAs
    Requires admin privileges.
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be an Excel file (.xlsx or .xls)")
    
    try:
        contents = await file.read()
        excel_file = BytesIO(contents)
        
        imported_counts = {"courses": 0, "instructors": 0, "tas": 0}
        
        # Try to import courses
        try:
            df_courses = pd.read_excel(excel_file, sheet_name='Courses')
            for _, row in df_courses.iterrows():
                try:
                    # Get level ID
                    level = db.query(models.Level).filter(
                        models.Level.level_name == row['Level']
                    ).first()
                    
                    if not level:
                        continue
                    
                    course = schemas.CourseCreate(
                        course_code=row['CourseCode'],
                        course_name=row['CourseName'],
                        level_id=level.level_id,
                        has_lab=bool(row.get('HasLab', 0)),
                        has_tutorial=bool(row.get('HasTutorial', 0)),
                        is_half_slot=bool(row.get('IsHalfSlot', 0))
                    )
                    crud.create_course(db, course)
                    imported_counts["courses"] += 1
                except Exception:
                    continue
        except Exception:
            pass
        
        # Try to import instructors
        try:
            df_instructors = pd.read_excel(excel_file, sheet_name='Instructors')
            for _, row in df_instructors.iterrows():
                try:
                    instructor = schemas.InstructorCreate(
                        instructor_name=row['InstructorName']
                    )
                    crud.create_instructor(db, instructor)
                    imported_counts["instructors"] += 1
                except Exception:
                    continue
        except Exception:
            pass
        
        # Try to import TAs
        try:
            df_tas = pd.read_excel(excel_file, sheet_name='TAs')
            for _, row in df_tas.iterrows():
                try:
                    ta = schemas.TACreate(ta_name=row['TAName'])
                    crud.create_ta(db, ta)
                    imported_counts["tas"] += 1
                except Exception:
                    continue
        except Exception:
            pass
        
        return {
            "message": "Data imported successfully",
            "imported": imported_counts
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to import data: {str(e)}")
