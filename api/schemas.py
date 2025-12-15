from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional, List
from enum import Enum


class RoomTypeEnum(str, Enum):
    THEATER = "Theater"
    CLASSROOM = "Classroom"
    LAB = "Lab"
    DRAWING_STUDIO = "Drawing Studio"


# Token schemas
class UserInfo(BaseModel):
    id: int
    username: str
    is_admin: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserInfo


class TokenData(BaseModel):
    username: Optional[str] = None


# User schemas
class UserCreate(BaseModel):
    username: str
    password: str
    is_admin: bool = False


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    user_id: int
    username: str
    is_admin: bool


# Building schemas
class BuildingCreate(BaseModel):
    building_name: str


class BuildingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    building_id: int
    building_name: str


# Hall schemas
class HallCreate(BaseModel):
    hall_name: str
    capacity: int


class HallResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    hall_id: int
    hall_name: str
    capacity: int


# Room schemas
class RoomCreate(BaseModel):
    building_id: int
    room_number: str
    room_type: RoomTypeEnum
    capacity: int


class RoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    room_id: int
    building_id: int
    room_number: str
    room_type: str
    capacity: int


# Level schemas
class LevelCreate(BaseModel):
    level_number: int  # 1, 2, 3, or 4
    specialization: Optional[str] = None
    num_sections: int
    num_groups_per_section: int
    total_students: int
    
    @field_validator('level_number')
    @classmethod
    def validate_level_number(cls, v):
        if v not in [1, 2, 3, 4]:
            raise ValueError("Level number must be 1, 2, 3, or 4")
        return v
    
    @field_validator('specialization')
    @classmethod
    def validate_specialization(cls, v, info):
        level_number = info.data.get('level_number')
        if level_number in [3, 4]:
            if not v or v.strip() == "":
                raise ValueError("Specialization is required for Level 3 and Level 4")
        elif level_number in [1, 2]:
            if v and v.strip() != "":
                raise ValueError("Specialization should not be provided for Level 1 and Level 2")
        return v


class LevelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    level_id: int
    level_name: str
    specialization: Optional[str]
    num_sections: int
    num_groups_per_section: int
    total_students: int


# Section schemas
class SectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    section_id: int
    level_id: int
    group_id: int
    section_number: int
    num_students: int


# Group schemas
class GroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    group_id: int
    level_id: int
    group_number: int
    num_students: int


# Course schemas
class CourseCreate(BaseModel):
    course_code: str
    course_name: str
    level_id: int
    lecture_slots: int = 1  # Number of lecture slots (default 1)
    lab_slots: float = 0  # Number of lab slots (0, 0.5, or 1)
    tutorial_slots: float = 0  # Number of tutorial slots (0, 0.5, or 1)
    
    @field_validator('lecture_slots')
    @classmethod
    def validate_lecture_slots(cls, v):
        if v < 1:
            raise ValueError("Course must have at least 1 lecture slot")
        return v
    
    @field_validator('lab_slots')
    @classmethod
    def validate_lab_slots(cls, v):
        if v not in [0, 0.5, 1]:
            raise ValueError("Lab slots must be 0, 0.5, or 1")
        return v
    
    @field_validator('tutorial_slots')
    @classmethod
    def validate_tutorial_slots(cls, v):
        if v not in [0, 0.5, 1]:
            raise ValueError("Tutorial slots must be 0, 0.5, or 1")
        return v


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    course_id: int
    course_code: str
    course_name: str
    level_id: int
    lecture_slots: int
    lab_slots: float
    tutorial_slots: float


# Instructor schemas
class InstructorCreate(BaseModel):
    instructor_name: str


class InstructorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    instructor_id: int
    instructor_name: str
    courses: List['CourseResponse'] = []


# TA schemas
class TACreate(BaseModel):
    ta_name: str


class TAResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    ta_id: int
    ta_name: str
    courses: List['CourseResponse'] = []


# Assignment schemas
class AssignInstructorRequest(BaseModel):
    instructor_id: int


class AssignTARequest(BaseModel):
    ta_id: int


# TimeSlot schemas
class TimeSlotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    timeslot_id: int
    day: str
    start_time: str
    end_time: str
    duration: int


# Schedule schemas
class ScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    schedule_id: int
    course_id: int
    group_id: int
    instructor_id: Optional[int]
    ta_id: Optional[int]
    room_id: int
    timeslot_id: int
    session_type: str


class ScheduleDetailResponse(BaseModel):
    day: str
    start_time: str
    end_time: str
    start_block: int  # Block number (0-7)
    duration_blocks: int  # 1 or 2 blocks (45 or 90 minutes)
    course_code: str
    course_name: str
    instructor_or_ta: str
    room_number: str
    building_name: str
    level_name: str
    level_id: Optional[int] = None
    section_number: Optional[int] = None
    group_number: Optional[int] = None
    session_type: str

