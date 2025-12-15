"""
Production-Grade University Timetable CSP Scheduler
Implements strict backtracking with 45-minute block system
"""
from sqlalchemy.orm import Session
from . import models
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Set, Dict, Tuple
import traceback


class ScheduleError(Exception):
    """Raised when schedule generation fails with specific reason"""
    pass


class SessionType(Enum):
    LECTURE = "LECTURE"
    LAB = "LAB"
    TUTORIAL = "TUTORIAL"


# Global 45-Minute Block System (8 blocks per day, 5 days = 40 total blocks)
BLOCKS_PER_DAY = 8
DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']

# Block -> Time mapping (45-minute intervals with breaks)
BLOCK_TIMES = {
    0: ('09:00', '09:45'),
    1: ('09:45', '10:30'),
    # BREAK: 10:30 - 10:45
    2: ('10:45', '11:30'),
    3: ('11:30', '12:15'),
    # BREAK: 12:15 - 12:30
    4: ('12:30', '13:15'),
    5: ('13:15', '14:00'),
    # BREAK: 14:00 - 14:15
    6: ('14:15', '15:00'),
    7: ('15:00', '15:45')
}

# Valid start blocks for 2-block sessions (cannot start at odd blocks)
VALID_START_BLOCKS = [0, 2, 4, 6]


@dataclass
class SessionVariable:
    """Represents a class session that needs to be scheduled"""
    var_id: int  # UNIQUE ID for each variable
    course_id: int
    course_code: str
    course_name: str
    session_type: SessionType
    duration_blocks: int  # 1 or 2 blocks
    student_count: int
    required_room_type: str  # "Lab", "Theater", "Classroom", "Studio"
    
    # Hierarchy info
    level_id: int
    group_id: Optional[int] = None  # For lectures
    group_number: Optional[int] = None
    section_id: Optional[int] = None  # For labs/tutorials
    section_number: Optional[int] = None
    
    def __hash__(self):
        return hash(self.var_id)
    
    def __eq__(self, other):
        if not isinstance(other, SessionVariable):
            return False
        return self.var_id == other.var_id
    
    def __str__(self):
        if self.session_type == SessionType.LECTURE:
            return f"Lecture (Course {self.course_code}, Group {self.group_number})"
        else:
            return f"{self.session_type.value} (Course {self.course_code}, Section {self.section_number})"


@dataclass
class Assignment:
    """Represents a scheduled session"""
    variable: SessionVariable
    day: str  # Sunday, Monday, etc.
    start_block: int  # 0-7
    end_block: int  # Exclusive (start_block + duration_blocks)
    room_id: int
    room_number: str
    building_name: str
    instructor_id: Optional[int] = None
    instructor_name: Optional[str] = None
    ta_id: Optional[int] = None
    ta_name: Optional[str] = None
    
    @property
    def start_time(self) -> str:
        return BLOCK_TIMES[self.start_block][0]
    
    @property
    def end_time(self) -> str:
        return BLOCK_TIMES[self.end_block - 1][1]


class CSPScheduler:
    """Production-grade CSP scheduler with strict validation"""
    
    def __init__(self, db: Session):
        self.db = db
        self.variables: List[SessionVariable] = []
        self.assignments: List[Assignment] = []
        
        # Cache for performance
        self.rooms_by_type: Dict[str, List] = {}
        self.instructors_by_course: Dict[int, List] = {}
        self.tas_by_course: Dict[int, List] = {}
        self.sections_by_group: Dict[int, List] = {}
        self.building_names: Dict[int, str] = {}  # Cache building names
        
    def generate_schedule(self) -> List[Dict]:
        """Main entry point - generates complete schedule"""
        try:
            print("\n" + "="*60)
            print("PRODUCTION CSP SCHEDULER - BLOCK SYSTEM")
            print("="*60)
            
            # Phase 1: Load and cache data
            self._load_cache()
            
            # Phase 2: Generate variables with fail-fast validation
            self._generate_variables()
            
            print(f"\n✓ Generated {len(self.variables)} session variables")
            print(f"  - Lectures: {sum(1 for v in self.variables if v.session_type == SessionType.LECTURE)}")
            print(f"  - Labs: {sum(1 for v in self.variables if v.session_type == SessionType.LAB)}")
            print(f"  - Tutorials: {sum(1 for v in self.variables if v.session_type == SessionType.TUTORIAL)}")
            
            # Phase 3: Backtracking search
            print("\n🔍 Starting backtracking search...")
            if not self._backtrack(0):
                raise ScheduleError("Could not find valid schedule. Constraints are too tight.")
            
            print(f"\n✓ Schedule generated successfully!")
            print(f"  Total assignments: {len(self.assignments)}")
            
            # Phase 4: Save to database
            return self._save_schedule()
            
        except ScheduleError as e:
            print(f"\n❌ Scheduling failed: {str(e)}")
            raise
        except Exception as e:
            print(f"\n❌ Unexpected error: {str(e)}")
            traceback.print_exc()
            raise ScheduleError(f"Scheduling error: {str(e)}")
    
    def _load_cache(self):
        """Load and cache all necessary data"""
        print("\n📊 Loading data...")
        
        # Load rooms by type
        rooms = self.db.query(models.Room).all()
        for room in rooms:
            if room.room_type not in self.rooms_by_type:
                self.rooms_by_type[room.room_type] = []
            self.rooms_by_type[room.room_type].append(room)
            # Cache building name
            self.building_names[room.building_id] = room.building.building_name
        
        print(f"  - Rooms: {len(rooms)} ({', '.join(f'{t}: {len(r)}' for t, r in self.rooms_by_type.items())})")
        
        # Load instructors and TAs by course
        courses = self.db.query(models.Course).all()
        for course in courses:
            self.instructors_by_course[course.course_id] = list(course.instructors)
            self.tas_by_course[course.course_id] = list(course.tas)
        
        print(f"  - Courses: {len(courses)}")
        
        # Load sections by group
        groups = self.db.query(models.Group).all()
        for group in groups:
            self.sections_by_group[group.group_id] = list(group.sections)
        
        print(f"  - Groups: {len(groups)}")
    
    def _generate_variables(self):
        """Generate all session variables with fail-fast capacity checks"""
        print("\n🔨 Generating variables with capacity validation...")
        
        courses = self.db.query(models.Course).all()
        var_id_counter = 0  # Unique ID counter
        
        for course in courses:
            print(f"\n  Course: {course.course_code} - {course.course_name}")
            
            # Get all groups for this course's level
            groups = self.db.query(models.Group).filter(
                models.Group.level_id == course.level_id
            ).all()
            
            for group in groups:
                # LECTURE: One per group (2 blocks)
                lecture_var = SessionVariable(
                    var_id=var_id_counter,
                    course_id=course.course_id,
                    course_code=course.course_code,
                    course_name=course.course_name,
                    session_type=SessionType.LECTURE,
                    duration_blocks=2,
                    student_count=group.num_students,
                    required_room_type="Theater" if group.num_students > 100 else "Classroom",
                    level_id=group.level_id,
                    group_id=group.group_id,
                    group_number=group.group_number
                )
                var_id_counter += 1
                
                # Fail-fast: Check if ANY room can accommodate this lecture
                if not self._capacity_check(lecture_var):
                    raise ScheduleError(
                        f"No {lecture_var.required_room_type} available for "
                        f"Lecture (Course {course.course_code}, Group {group.group_number}) "
                        f"with {lecture_var.student_count} students"
                    )
                
                self.variables.append(lecture_var)
                print(f"    ✓ Lecture for Group {group.group_number} ({lecture_var.student_count} students)")
                
                # Get sections in this group
                sections = self.db.query(models.Section).filter(
                    models.Section.group_id == group.group_id
                ).all()
                
                for section in sections:
                    # LAB: One per section (2 blocks)
                    lab_var = SessionVariable(
                        var_id=var_id_counter,
                        course_id=course.course_id,
                        course_code=course.course_code,
                        course_name=course.course_name,
                        session_type=SessionType.LAB,
                        duration_blocks=2,
                        student_count=section.num_students,
                        required_room_type="Lab",
                        level_id=section.level_id,
                        group_id=group.group_id,
                        group_number=group.group_number,
                        section_id=section.section_id,
                        section_number=section.section_number
                    )
                    var_id_counter += 1
                    
                    if not self._capacity_check(lab_var):
                        raise ScheduleError(
                            f"No Lab available for Section {section.section_number} "
                            f"with {lab_var.student_count} students"
                        )
                    
                    self.variables.append(lab_var)
                    
                    # TUTORIAL: One per section (2 blocks for standard, 1 for small)
                    # Use 1 block if section has <= 15 students
                    duration = 1 if section.num_students <= 15 else 2
                    
                    tutorial_var = SessionVariable(
                        var_id=var_id_counter,
                        course_id=course.course_id,
                        course_code=course.course_code,
                        course_name=course.course_name,
                        session_type=SessionType.TUTORIAL,
                        duration_blocks=duration,
                        student_count=section.num_students,
                        required_room_type="Classroom",
                        level_id=section.level_id,
                        group_id=group.group_id,
                        group_number=group.group_number,
                        section_id=section.section_id,
                        section_number=section.section_number
                    )
                    var_id_counter += 1
                    
                    if not self._capacity_check(tutorial_var):
                        raise ScheduleError(
                            f"No Classroom available for Tutorial (Section {section.section_number}) "
                            f"with {tutorial_var.student_count} students"
                        )
                    
                    self.variables.append(tutorial_var)
                    print(f"      ✓ Lab + Tutorial for Section {section.section_number} ({section.num_students} students)")
    
    def _capacity_check(self, variable: SessionVariable) -> bool:
        """Fail-fast: Check if ANY room can accommodate this session"""
        room_type = variable.required_room_type
        student_count = variable.student_count
        
        if room_type not in self.rooms_by_type:
            return False
        
        # Check if at least one room of this type has sufficient capacity
        for room in self.rooms_by_type[room_type]:
            if room.capacity >= student_count:
                return True
        
        return False
    
    def _backtrack(self, var_index: int) -> bool:
        """Recursive backtracking with strict constraint checking"""
        # Base case: all variables assigned
        if var_index >= len(self.variables):
            return True
        
        variable = self.variables[var_index]
        
        # Generate domain for this variable
        domain = self._generate_domain(variable)
        
        if len(domain) == 0:
            print(f"    ⚠ No valid assignments for {variable}")
            return False
        
        # Try each assignment in the domain
        for assignment in domain:
            if self._is_valid(assignment):
                # Make assignment
                self.assignments.append(assignment)
                
                # Recurse
                if self._backtrack(var_index + 1):
                    return True
                
                # Backtrack
                self.assignments.pop()
        
        return False
    
    def _generate_domain(self, variable: SessionVariable) -> List[Assignment]:
        """Generate all possible assignments for a variable"""
        domain = []
        room_type = variable.required_room_type
        
        # Get suitable rooms
        suitable_rooms = [
            room for room in self.rooms_by_type.get(room_type, [])
            if room.capacity >= variable.student_count
        ]
        
        # ROLE-BASED FILTERING: Lectures = Instructors ONLY, Labs/Tutorials = TAs ONLY
        if variable.session_type == SessionType.LECTURE:
            # Lectures can ONLY be taught by Instructors (Doctors)
            instructors = self.instructors_by_course.get(variable.course_id, [])
            if not instructors:
                return []
            staff_list = instructors
            staff_type = 'instructor'
        else:
            # Labs and Tutorials can ONLY be taught by TAs
            tas = self.tas_by_course.get(variable.course_id, [])
            if not tas:
                return []
            staff_list = tas
            staff_type = 'ta'
        
        # Generate assignments for each day and valid block
        for day in DAYS:
            # BLOCK VALIDATION:
            # - 2-block sessions (90 min): Must start at EVEN blocks (0, 2, 4, 6)
            # - 1-block sessions (45 min): Can start at ANY block (0-7)
            if variable.duration_blocks == 2:
                # Standard sessions must start at even blocks to avoid breaks
                valid_blocks = VALID_START_BLOCKS
            else:
                # Small tutorials can start at any block
                valid_blocks = list(range(BLOCKS_PER_DAY))
            
            for start_block in valid_blocks:
                end_block = start_block + variable.duration_blocks
                
                # Check if end_block is within bounds
                if end_block > BLOCKS_PER_DAY:
                    continue
                
                for room in suitable_rooms:
                    for staff in staff_list:
                        if staff_type == 'instructor':
                            assignment = Assignment(
                                variable=variable,
                                day=day,
                                start_block=start_block,
                                end_block=end_block,
                                room_id=room.room_id,
                                room_number=room.room_number,
                                building_name=self.building_names[room.building_id],
                                instructor_id=staff.instructor_id,
                                instructor_name=staff.instructor_name
                            )
                        else:
                            assignment = Assignment(
                                variable=variable,
                                day=day,
                                start_block=start_block,
                                end_block=end_block,
                                room_id=room.room_id,
                                room_number=room.room_number,
                                building_name=self.building_names[room.building_id],
                                ta_id=staff.ta_id,
                                ta_name=staff.ta_name
                            )
                        domain.append(assignment)
        
        return domain
    
    def _is_valid(self, assignment: Assignment) -> bool:
        """Check if assignment satisfies all hard constraints"""
        var = assignment.variable
        
        # CRITICAL: Check if this variable has already been scheduled (SINGLETON RULE)
        for existing in self.assignments:
            if existing.variable.var_id == var.var_id:
                return False  # This specific variable has already been assigned a time slot
        
        for existing in self.assignments:
            # Check if assignments overlap in time (same day and overlapping blocks)
            if assignment.day == existing.day:
                # Check block overlap
                overlap = not (assignment.end_block <= existing.start_block or 
                              assignment.start_block >= existing.end_block)
                
                if overlap:
                    # A. Room Conflict
                    if assignment.room_id == existing.room_id:
                        return False
                    
                    # B. Instructor/TA Conflict
                    if assignment.instructor_id and assignment.instructor_id == existing.instructor_id:
                        return False
                    if assignment.ta_id and assignment.ta_id == existing.ta_id:
                        return False
                    
                    # C. Hierarchical Conflicts
                    if not self._check_hierarchy(var, existing.variable):
                        return False
        
        return True
    
    def _check_hierarchy(self, var1: SessionVariable, var2: SessionVariable) -> bool:
        """
        Check hierarchical constraints (Container Rules)
        Returns False if there's a conflict
        """
        # Rule 1: Same group cannot be in two places
        if (var1.session_type == SessionType.LECTURE and 
            var2.session_type == SessionType.LECTURE and 
            var1.group_id == var2.group_id):
            return False
        
        # Rule 2: If a group has a lecture, its sections cannot have lab/tutorial
        if var1.session_type == SessionType.LECTURE and var2.session_type != SessionType.LECTURE:
            # Check if var2's section belongs to var1's group
            if var2.group_id == var1.group_id:
                return False
        
        if var2.session_type == SessionType.LECTURE and var1.session_type != SessionType.LECTURE:
            # Check if var1's section belongs to var2's group
            if var1.group_id == var2.group_id:
                return False
        
        # Rule 3: Same section cannot be in two places
        if (var1.section_id and var2.section_id and 
            var1.section_id == var2.section_id and 
            var1.session_type != SessionType.LECTURE and 
            var2.session_type != SessionType.LECTURE):
            return False
        
        return True
    
    def _save_schedule(self) -> List[Dict]:
        """Save schedule to database and return JSON"""
        print("\n💾 Saving schedule to database...")
        
        # Clear existing schedule
        self.db.query(models.Schedule).delete()
        self.db.commit()
        
        result = []
        
        for assignment in self.assignments:
            var = assignment.variable
            
            # Find or create timeslot for this day/time combination
            duration_minutes = 90 if var.duration_blocks == 2 else 45
            timeslot = self.db.query(models.TimeSlot).filter(
                models.TimeSlot.day == assignment.day,
                models.TimeSlot.start_time == assignment.start_time + ":00",
                models.TimeSlot.end_time == assignment.end_time + ":00"
            ).first()
            
            if not timeslot:
                # Create new timeslot
                timeslot = models.TimeSlot(
                    day=assignment.day,
                    start_time=assignment.start_time + ":00",
                    end_time=assignment.end_time + ":00",
                    duration=duration_minutes
                )
                self.db.add(timeslot)
                self.db.flush()  # Get the timeslot_id
            
            # For labs/tutorials, use the section's group_id
            # For lectures, use the lecture's group_id
            group_id = var.group_id
            
            # Create schedule entry
            schedule_entry = models.Schedule(
                course_id=var.course_id,
                group_id=group_id,
                section_id=var.section_id,  # Save section_id for labs/tutorials (None for lectures)
                timeslot_id=timeslot.timeslot_id,
                room_id=assignment.room_id,
                instructor_id=assignment.instructor_id,
                ta_id=assignment.ta_id,
                session_type=var.session_type.value
            )
            
            self.db.add(schedule_entry)
            
            # Build JSON response with section_name and group_name
            result.append({
                "type": var.session_type.value,
                "course_code": var.course_code,
                "course_name": var.course_name,
                "duration_blocks": var.duration_blocks,
                "day": assignment.day,
                "start_time": assignment.start_time,
                "end_time": assignment.end_time,
                "start_block": assignment.start_block,
                "end_block": assignment.end_block,
                "room_name": assignment.room_number,
                "building_name": assignment.building_name,
                "instructor_or_ta": assignment.instructor_name or assignment.ta_name,
                "level_id": var.level_id,
                "group_id": var.group_id,
                "group_name": f"Group {var.group_number}" if var.group_number else None,
                "group_number": var.group_number,
                "section_id": var.section_id,
                "section_name": f"Section {var.section_number}" if var.section_number else None,
                "section_number": var.section_number,
                "student_count": var.student_count
            })
        
        self.db.commit()
        print(f"  ✓ Saved {len(result)} schedule entries")
        
        return result
