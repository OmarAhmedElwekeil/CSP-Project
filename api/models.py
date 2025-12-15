from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table, Float
from sqlalchemy.orm import relationship
from api.database import Base


# Many-to-Many association tables
instructor_qualified_courses = Table(
    'instructor_qualified_courses',
    Base.metadata,
    Column('instructor_id', Integer, ForeignKey('instructors.instructor_id', ondelete='CASCADE'), primary_key=True),
    Column('course_id', Integer, ForeignKey('courses.course_id', ondelete='CASCADE'), primary_key=True)
)

ta_qualified_courses = Table(
    'ta_qualified_courses',
    Base.metadata,
    Column('ta_id', Integer, ForeignKey('tas.ta_id', ondelete='CASCADE'), primary_key=True),
    Column('course_id', Integer, ForeignKey('courses.course_id', ondelete='CASCADE'), primary_key=True)
)


class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)


class Building(Base):
    __tablename__ = 'buildings'
    
    building_id = Column(Integer, primary_key=True, index=True)
    building_name = Column(String, unique=True, nullable=False)
    
    rooms = relationship("Room", back_populates="building", cascade="all, delete-orphan")


class Hall(Base):
    __tablename__ = 'halls'
    
    hall_id = Column(Integer, primary_key=True, index=True)
    hall_name = Column(String, unique=True, nullable=False)
    capacity = Column(Integer, nullable=False)


class Room(Base):
    __tablename__ = 'rooms'
    
    room_id = Column(Integer, primary_key=True, index=True)
    building_id = Column(Integer, ForeignKey('buildings.building_id', ondelete='CASCADE'), nullable=False)
    room_number = Column(String, nullable=False)
    room_type = Column(String, nullable=False)  # Theater, Classroom, Lab, Drawing Studio
    capacity = Column(Integer, nullable=False)
    
    building = relationship("Building", back_populates="rooms")
    schedules = relationship("Schedule", back_populates="room", cascade="all, delete-orphan")


class Level(Base):
    __tablename__ = 'levels'
    
    level_id = Column(Integer, primary_key=True, index=True)
    level_name = Column(String, unique=True, nullable=False)
    specialization = Column(String, nullable=True)
    num_sections = Column(Integer, nullable=False)
    num_groups_per_section = Column(Integer, nullable=False)
    total_students = Column(Integer, nullable=False)
    
    sections = relationship("Section", back_populates="level", cascade="all, delete-orphan")
    groups = relationship("Group", back_populates="level", cascade="all, delete-orphan")
    courses = relationship("Course", back_populates="level", cascade="all, delete-orphan")


class Section(Base):
    __tablename__ = 'sections'
    
    section_id = Column(Integer, primary_key=True, index=True)
    level_id = Column(Integer, ForeignKey('levels.level_id', ondelete='CASCADE'), nullable=False)
    group_id = Column(Integer, ForeignKey('groups.group_id', ondelete='CASCADE'), nullable=False)
    section_number = Column(Integer, nullable=False)
    num_students = Column(Integer, nullable=False)
    
    level = relationship("Level", back_populates="sections")
    group = relationship("Group", back_populates="sections")
    schedules = relationship("Schedule", back_populates="section", cascade="all, delete-orphan")


class Group(Base):
    __tablename__ = 'groups'
    
    group_id = Column(Integer, primary_key=True, index=True)
    level_id = Column(Integer, ForeignKey('levels.level_id', ondelete='CASCADE'), nullable=False)
    group_number = Column(Integer, nullable=False)
    num_students = Column(Integer, nullable=False)
    
    level = relationship("Level", back_populates="groups")
    sections = relationship("Section", back_populates="group", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="group", cascade="all, delete-orphan")


class Course(Base):
    __tablename__ = 'courses'
    
    course_id = Column(Integer, primary_key=True, index=True)
    course_code = Column(String, unique=True, nullable=False)
    course_name = Column(String, nullable=False)
    level_id = Column(Integer, ForeignKey('levels.level_id', ondelete='CASCADE'), nullable=False)
    lecture_slots = Column(Integer, default=1, nullable=False)
    lab_slots = Column(Float, default=0.0, nullable=False)
    tutorial_slots = Column(Float, default=0.0, nullable=False)
    
    level = relationship("Level", back_populates="courses")
    instructors = relationship("Instructor", secondary=instructor_qualified_courses, back_populates="courses")
    tas = relationship("TA", secondary=ta_qualified_courses, back_populates="courses")
    schedules = relationship("Schedule", back_populates="course", cascade="all, delete-orphan")


class Instructor(Base):
    __tablename__ = 'instructors'
    
    instructor_id = Column(Integer, primary_key=True, index=True)
    instructor_name = Column(String, unique=True, nullable=False)
    
    courses = relationship("Course", secondary=instructor_qualified_courses, back_populates="instructors")
    schedules = relationship("Schedule", back_populates="instructor")


class TA(Base):
    __tablename__ = 'tas'
    
    ta_id = Column(Integer, primary_key=True, index=True)
    ta_name = Column(String, unique=True, nullable=False)
    
    courses = relationship("Course", secondary=ta_qualified_courses, back_populates="tas")
    schedules = relationship("Schedule", back_populates="ta")


class TimeSlot(Base):
    __tablename__ = 'timeslots'
    
    timeslot_id = Column(Integer, primary_key=True, index=True)
    day = Column(String, nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)  # in minutes (90 or 45)
    
    schedules = relationship("Schedule", back_populates="timeslot", cascade="all, delete-orphan")


class Schedule(Base):
    __tablename__ = 'schedule'
    
    schedule_id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey('courses.course_id', ondelete='CASCADE'), nullable=False)
    group_id = Column(Integer, ForeignKey('groups.group_id', ondelete='CASCADE'), nullable=False)
    section_id = Column(Integer, ForeignKey('sections.section_id', ondelete='CASCADE'), nullable=True)  # For labs/tutorials
    instructor_id = Column(Integer, ForeignKey('instructors.instructor_id', ondelete='SET NULL'), nullable=True)
    ta_id = Column(Integer, ForeignKey('tas.ta_id', ondelete='SET NULL'), nullable=True)
    room_id = Column(Integer, ForeignKey('rooms.room_id', ondelete='CASCADE'), nullable=False)
    timeslot_id = Column(Integer, ForeignKey('timeslots.timeslot_id', ondelete='CASCADE'), nullable=False)
    session_type = Column(String, nullable=False)  # Lecture, Lab, Tutorial
    
    course = relationship("Course", back_populates="schedules")
    group = relationship("Group", back_populates="schedules")
    section = relationship("Section", back_populates="schedules")
    instructor = relationship("Instructor", back_populates="schedules")
    ta = relationship("TA", back_populates="schedules")
    room = relationship("Room", back_populates="schedules")
    timeslot = relationship("TimeSlot", back_populates="schedules")
