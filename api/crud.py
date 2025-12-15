from sqlalchemy.orm import Session
from api import models, schemas
from typing import List, Optional


# Building CRUD
def create_building(db: Session, building: schemas.BuildingCreate):
    db_building = models.Building(building_name=building.building_name)
    db.add(db_building)
    db.commit()
    db.refresh(db_building)
    return db_building


def get_building(db: Session, building_id: int):
    return db.query(models.Building).filter(models.Building.building_id == building_id).first()


def get_buildings(db: Session):
    return db.query(models.Building).all()


def update_building(db: Session, building_id: int, building: schemas.BuildingCreate):
    db_building = get_building(db, building_id)
    if db_building:
        db_building.building_name = building.building_name
        db.commit()
        db.refresh(db_building)
        return db_building
    return None


def delete_building(db: Session, building_id: int):
    db_building = get_building(db, building_id)
    if db_building:
        db.delete(db_building)
        db.commit()
        return True
    return False


# Hall CRUD
def create_hall(db: Session, hall: schemas.HallCreate):
    db_hall = models.Hall(
        hall_name=hall.hall_name,
        capacity=hall.capacity
    )
    db.add(db_hall)
    db.commit()
    db.refresh(db_hall)
    return db_hall


def get_hall(db: Session, hall_id: int):
    return db.query(models.Hall).filter(models.Hall.hall_id == hall_id).first()


def get_halls(db: Session):
    return db.query(models.Hall).all()


def update_hall(db: Session, hall_id: int, hall: schemas.HallCreate):
    db_hall = get_hall(db, hall_id)
    if db_hall:
        db_hall.hall_name = hall.hall_name
        db_hall.capacity = hall.capacity
        db.commit()
        db.refresh(db_hall)
        return db_hall
    return None


def delete_hall(db: Session, hall_id: int):
    db_hall = get_hall(db, hall_id)
    if db_hall:
        db.delete(db_hall)
        db.commit()
        return True
    return False


# Room CRUD
def create_room(db: Session, room: schemas.RoomCreate):
    db_room = models.Room(
        building_id=room.building_id,
        room_number=room.room_number,
        room_type=room.room_type.value,
        capacity=room.capacity
    )
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room


def get_room(db: Session, room_id: int):
    return db.query(models.Room).filter(models.Room.room_id == room_id).first()


def get_rooms(db: Session, building_id: Optional[int] = None):
    query = db.query(models.Room)
    if building_id:
        query = query.filter(models.Room.building_id == building_id)
    return query.all()


def update_room(db: Session, room_id: int, room: schemas.RoomCreate):
    db_room = get_room(db, room_id)
    if db_room:
        db_room.building_id = room.building_id
        db_room.room_number = room.room_number
        db_room.room_type = room.room_type.value
        db_room.capacity = room.capacity
        db.commit()
        db.refresh(db_room)
        return db_room
    return None


def delete_room(db: Session, room_id: int):
    db_room = get_room(db, room_id)
    if db_room:
        db.delete(db_room)
        db.commit()
        return True
    return False


# Level CRUD
def create_level(db: Session, level: schemas.LevelCreate):
    """Create level and automatically generate groups and sections"""
    # Generate level name from number
    level_name = f"Level {level.level_number}"
    if level.specialization:
        level_name += f" - {level.specialization}"
    
    db_level = models.Level(
        level_name=level_name,
        specialization=level.specialization,
        num_sections=level.num_sections,
        num_groups_per_section=level.num_groups_per_section,
        total_students=level.total_students
    )
    db.add(db_level)
    db.commit()
    db.refresh(db_level)
    
    # Auto-create groups first, then sections
    # num_groups_per_section now means "number of sections per group"
    # So we need num_sections to be >= num_groups_per_section
    total_groups = level.num_sections  # Total number of groups
    sections_per_group = level.num_groups_per_section  # Sections inside each group
    
    students_per_group = level.total_students // total_groups
    remainder_students = level.total_students % total_groups
    
    global_section_number = 1  # Incremental section numbering across all groups
    
    for group_num in range(1, total_groups + 1):
        # Add remainder students to first groups
        group_students = students_per_group + (1 if group_num <= remainder_students else 0)
        section_remainder = group_students % sections_per_group
        base_section_students = group_students // sections_per_group
        
        db_group = models.Group(
            level_id=db_level.level_id,
            group_number=group_num,
            num_students=group_students
        )
        db.add(db_group)
        db.commit()
        db.refresh(db_group)
        
        for section_idx in range(sections_per_group):
            # Distribute remainder among first sections within this group
            section_students = base_section_students + (1 if section_idx < section_remainder else 0)
            db_section = models.Section(
                level_id=db_level.level_id,
                group_id=db_group.group_id,
                section_number=global_section_number,
                num_students=section_students
            )
            db.add(db_section)
            global_section_number += 1
    
    db.commit()
    db.refresh(db_level)
    return db_level


def get_level(db: Session, level_id: int):
    return db.query(models.Level).filter(models.Level.level_id == level_id).first()


def get_levels(db: Session):
    return db.query(models.Level).all()


def get_level_sections(db: Session, level_id: int):
    return db.query(models.Section).filter(models.Section.level_id == level_id).all()


def get_level_groups(db: Session, level_id: int):
    return db.query(models.Group).filter(models.Group.level_id == level_id).all()


def delete_level(db: Session, level_id: int):
    db_level = get_level(db, level_id)
    if db_level:
        db.delete(db_level)
        db.commit()
        return True
    return False


def update_level(db: Session, level_id: int, level: schemas.LevelCreate):
    db_level = get_level(db, level_id)
    if not db_level:
        return None
    
    # Generate level name from number (same as create)
    level_name = f"Level {level.level_number}"
    if level.specialization:
        level_name += f" - {level.specialization}"
    
    # Update basic fields
    db_level.level_name = level_name
    db_level.specialization = level.specialization
    db_level.total_students = level.total_students
    
    # If structure changed, recreate sections and groups
    if (db_level.num_sections != level.num_sections or 
        db_level.num_groups_per_section != level.num_groups_per_section):
        
        # Delete existing sections and groups
        db.query(models.Section).filter(models.Section.level_id == level_id).delete()
        db.query(models.Group).filter(models.Group.level_id == level_id).delete()
        
        # Update structure fields
        db_level.num_sections = level.num_sections
        db_level.num_groups_per_section = level.num_groups_per_section
        
        # Recreate groups and sections (same as create)
        total_groups = level.num_sections
        sections_per_group = level.num_groups_per_section
        students_per_group = level.total_students // total_groups
        remainder_students = level.total_students % total_groups
        
        global_section_number = 1  # Incremental section numbering
        
        for group_num in range(1, total_groups + 1):
            # Add remainder students to first groups
            group_students = students_per_group + (1 if group_num <= remainder_students else 0)
            section_remainder = group_students % sections_per_group
            base_section_students = group_students // sections_per_group
            
            group = models.Group(
                level_id=level_id,
                group_number=group_num,
                num_students=group_students
            )
            db.add(group)
            db.flush()
            
            for section_idx in range(sections_per_group):
                # Distribute remainder among first sections within this group
                section_students = base_section_students + (1 if section_idx < section_remainder else 0)
                section = models.Section(
                    level_id=level_id,
                    group_id=group.group_id,
                    section_number=global_section_number,
                    num_students=section_students
                )
                db.add(section)
                global_section_number += 1
    else:
        # Only student count changed - update existing groups and sections
        total_groups = level.num_sections
        sections_per_group = level.num_groups_per_section
        students_per_group = level.total_students // total_groups
        remainder_students = level.total_students % total_groups
        
        # Update all groups for this level
        groups = db.query(models.Group).filter(models.Group.level_id == level_id).order_by(models.Group.group_number).all()
        for idx, group in enumerate(groups, 1):
            group_students = students_per_group + (1 if idx <= remainder_students else 0)
            group.num_students = group_students
            
            # Update sections for this group
            section_remainder = group_students % sections_per_group
            base_section_students = group_students // sections_per_group
            sections = db.query(models.Section).filter(models.Section.group_id == group.group_id).order_by(models.Section.section_number).all()
            for sec_idx, section in enumerate(sections, 1):
                section.num_students = base_section_students + (1 if sec_idx <= section_remainder else 0)
    
    db.commit()
    db.refresh(db_level)
    return db_level


# Section CRUD
def get_section(db: Session, section_id: int):
    return db.query(models.Section).filter(models.Section.section_id == section_id).first()


def get_sections(db: Session):
    return db.query(models.Section).all()


def delete_section(db: Session, section_id: int):
    db_section = get_section(db, section_id)
    if db_section:
        db.delete(db_section)
        db.commit()
        return True
    return False


# Group CRUD
def get_group(db: Session, group_id: int):
    return db.query(models.Group).filter(models.Group.group_id == group_id).first()


def get_groups(db: Session):
    return db.query(models.Group).all()


def get_group_sections(db: Session, group_id: int):
    """Get all sections belonging to a specific group"""
    return db.query(models.Section).filter(models.Section.group_id == group_id).all()


def delete_group(db: Session, group_id: int):
    db_group = get_group(db, group_id)
    if db_group:
        db.delete(db_group)
        db.commit()
        return True
    return False


# Course CRUD
def create_course(db: Session, course: schemas.CourseCreate):
    db_course = models.Course(
        course_code=course.course_code,
        course_name=course.course_name,
        level_id=course.level_id,
        lecture_slots=course.lecture_slots,
        lab_slots=course.lab_slots,
        tutorial_slots=course.tutorial_slots
    )
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course


def get_course(db: Session, course_id: int):
    return db.query(models.Course).filter(models.Course.course_id == course_id).first()


def get_courses(db: Session, level_id: Optional[int] = None):
    query = db.query(models.Course)
    if level_id:
        query = query.filter(models.Course.level_id == level_id)
    return query.all()


def update_course(db: Session, course_id: int, course: schemas.CourseCreate):
    db_course = get_course(db, course_id)
    if db_course:
        db_course.course_code = course.course_code
        db_course.course_name = course.course_name
        db_course.level_id = course.level_id
        db_course.lecture_slots = course.lecture_slots
        db_course.lab_slots = course.lab_slots
        db_course.tutorial_slots = course.tutorial_slots
        db.commit()
        db.refresh(db_course)
        return db_course
    return None


def delete_course(db: Session, course_id: int):
    db_course = get_course(db, course_id)
    if db_course:
        db.delete(db_course)
        db.commit()
        return True
    return False


def assign_instructor_to_course(db: Session, course_id: int, instructor_id: int):
    db_course = get_course(db, course_id)
    db_instructor = get_instructor(db, instructor_id)
    
    if db_course and db_instructor:
        if db_instructor not in db_course.instructors:
            db_course.instructors.append(db_instructor)
            db.commit()
        return True
    return False


def assign_ta_to_course(db: Session, course_id: int, ta_id: int):
    db_course = get_course(db, course_id)
    db_ta = get_ta(db, ta_id)
    
    if db_course and db_ta:
        if db_ta not in db_course.tas:
            db_course.tas.append(db_ta)
            db.commit()
        return True
    return False


# Instructor CRUD
def create_instructor(db: Session, instructor: schemas.InstructorCreate):
    db_instructor = models.Instructor(instructor_name=instructor.instructor_name)
    db.add(db_instructor)
    db.commit()
    db.refresh(db_instructor)
    return db_instructor


def get_instructor(db: Session, instructor_id: int):
    return db.query(models.Instructor).filter(models.Instructor.instructor_id == instructor_id).first()


def get_instructors(db: Session):
    return db.query(models.Instructor).all()


def get_instructor_courses(db: Session, instructor_id: int):
    db_instructor = get_instructor(db, instructor_id)
    return db_instructor.courses if db_instructor else []


def update_instructor(db: Session, instructor_id: int, instructor: schemas.InstructorCreate):
    db_instructor = get_instructor(db, instructor_id)
    if db_instructor:
        db_instructor.instructor_name = instructor.instructor_name
        db.commit()
        db.refresh(db_instructor)
        return db_instructor
    return None


def delete_instructor(db: Session, instructor_id: int):
    db_instructor = get_instructor(db, instructor_id)
    if db_instructor:
        db.delete(db_instructor)
        db.commit()
        return True
    return False


# TA CRUD
def create_ta(db: Session, ta: schemas.TACreate):
    db_ta = models.TA(ta_name=ta.ta_name)
    db.add(db_ta)
    db.commit()
    db.refresh(db_ta)
    return db_ta


def get_ta(db: Session, ta_id: int):
    return db.query(models.TA).filter(models.TA.ta_id == ta_id).first()


def get_tas(db: Session):
    return db.query(models.TA).all()


def get_ta_courses(db: Session, ta_id: int):
    db_ta = get_ta(db, ta_id)
    return db_ta.courses if db_ta else []


def update_ta(db: Session, ta_id: int, ta: schemas.TACreate):
    db_ta = get_ta(db, ta_id)
    if db_ta:
        db_ta.ta_name = ta.ta_name
        db.commit()
        db.refresh(db_ta)
        return db_ta
    return None


def delete_ta(db: Session, ta_id: int):
    db_ta = get_ta(db, ta_id)
    if db_ta:
        db.delete(db_ta)
        db.commit()
        return True
    return False


# Schedule CRUD
def get_schedule(
    db: Session,
    day: Optional[str] = None,
    instructor_id: Optional[int] = None,
    ta_id: Optional[int] = None,
    course_id: Optional[int] = None,
    group_id: Optional[int] = None,
    room_id: Optional[int] = None
):
    query = db.query(models.Schedule)
    
    if day:
        query = query.join(models.TimeSlot).filter(models.TimeSlot.day == day)
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
    
    return query.all()


def clear_schedule(db: Session):
    db.query(models.Schedule).delete()
    db.commit()


# User CRUD (for authentication)
def create_user(db: Session, user: schemas.UserCreate, hashed_password: str):
    db_user = models.User(
        username=user.username,
        hashed_password=hashed_password,
        is_admin=user.is_admin
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()
