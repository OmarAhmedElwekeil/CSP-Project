from sqlalchemy.orm import Session
from sqlalchemy import and_, exists
from api import models
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class SessionType(Enum):
    LECTURE = "Lecture"
    LAB = "Lab"
    TUTORIAL = "Tutorial"


@dataclass
class Variable:
    """Represents a class session that needs to be scheduled"""
    course_id: int
    session_type: SessionType
    group_id: Optional[int] = None  # For lectures
    section_id: Optional[int] = None  # For labs/tutorials
    duration: int = 90  # minutes
    
    def __hash__(self):
        return hash((self.course_id, self.session_type.value, self.group_id, self.section_id))
    
    def __str__(self):
        if self.session_type == SessionType.LECTURE:
            return f"{self.session_type.value} (Course {self.course_id}, Group {self.group_id})"
        else:
            return f"{self.session_type.value} (Course {self.course_id}, Section {self.section_id})"


@dataclass
class Assignment:
    """Represents a time/room/instructor assignment for a variable"""
    variable: Variable
    timeslot_id: int
    room_id: int
    instructor_id: Optional[int] = None
    ta_id: Optional[int] = None


class CSPScheduler:
    """Constraint Satisfaction Problem Scheduler for timetable generation"""
    
    def __init__(self, db: Session):
        self.db = db
        self.variables: List[Variable] = []
        self.assignments: List[Assignment] = []
        
    def generate_schedule(self) -> Tuple[bool, str]:
        """
        Generate the complete schedule using CSP algorithm with backtracking.
        Returns: (success: bool, message: str)
        """
        try:
            # Clear existing schedule
            self.db.query(models.Schedule).delete()
            self.db.commit()
            
            # Phase 1: Generate all variables (the "to-do list")
            self.variables = self._generate_variables()
            
            if not self.variables:
                return False, "No courses found to schedule"
            
            print(f"DEBUG: Generated {len(self.variables)} variables")
            for v in self.variables[:5]:  # Print first 5
                print(f"  {v}")
            
            # Phase 2: Sort variables by constraint (Most Constrained First)
            self.variables.sort(key=self._constraint_score, reverse=True)
            
            # Phase 3 & 4: Backtracking solver
            self.assignments = []
            if self._backtrack(0):
                # Save all assignments to database
                self._save_to_database()
                self.db.commit()
                return True, f"Schedule generated successfully with {len(self.assignments)} sessions"
            else:
                return False, "Could not find a valid schedule. Try adding more rooms or time slots."
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.db.rollback()
            return False, f"Error: {str(e)}"
    
    def _generate_variables(self) -> List[Variable]:
        """Phase 1: Generate all variables that need to be scheduled"""
        variables = []
        courses = self.db.query(models.Course).all()
        
        for course in courses:
            # Get all groups for this course's level
            groups = self.db.query(models.Group).filter(
                models.Group.level_id == course.level_id
            ).all()
            
            if not groups:
                continue
            
            # Mandatory: 1 Lecture per Group (90 minutes)
            for group in groups:
                variables.append(Variable(
                    course_id=course.course_id,
                    session_type=SessionType.LECTURE,
                    group_id=group.group_id,
                    duration=90
                ))
            
            # Optional: Labs for each Section (if course has labs)
            if course.lab_slots > 0:
                sections = self.db.query(models.Section).join(
                    models.Group
                ).filter(
                    models.Group.level_id == course.level_id
                ).all()
                
                for section in sections:
                    variables.append(Variable(
                        course_id=course.course_id,
                        session_type=SessionType.LAB,
                        section_id=section.section_id,
                        duration=90  # Labs are always 90 minutes
                    ))
            
            # Optional: Tutorials for each Section (if course has tutorials)
            if course.tutorial_slots > 0:
                sections = self.db.query(models.Section).join(
                    models.Group
                ).filter(
                    models.Group.level_id == course.level_id
                ).all()
                
                for section in sections:
                    # Check if it's a half-slot tutorial (45 min) or full (90 min)
                    duration = 45 if course.tutorial_slots == 0.5 else 90
                    variables.append(Variable(
                        course_id=course.course_id,
                        session_type=SessionType.TUTORIAL,
                        section_id=section.section_id,
                        duration=duration
                    ))
        
        return variables
    
    def _constraint_score(self, var: Variable) -> int:
        """Calculate constraint score for sorting (higher = more constrained)"""
        score = 0
        
        # Lectures are more constrained (need larger rooms, affect all sections)
        if var.session_type == SessionType.LECTURE:
            score += 100
            # Get group size
            group = self.db.query(models.Group).get(var.group_id)
            if group:
                score += group.num_students  # Larger groups are harder to place
        
        # 90-minute sessions are more constrained than 45-minute
        if var.duration == 90:
            score += 50
        
        return score
    
    def _backtrack(self, var_index: int) -> bool:
        """Phase 4: Backtracking solver"""
        # Base case: all variables assigned
        if var_index >= len(self.variables):
            return True
        
        variable = self.variables[var_index]
        
        # Get domain (all possible timeslot, room, instructor combinations)
        domain = self._get_domain(variable)
        
        print(f"DEBUG: Variable {var_index+1}/{len(self.variables)}: {variable}")
        print(f"DEBUG: Domain size: {len(domain)} combinations")
        
        if len(domain) == 0:
            print(f"DEBUG: EMPTY DOMAIN - No valid (timeslot, room, instructor/TA) combinations!")
            return False
        
        for timeslot_id, room_id, instructor_id, ta_id in domain:
            assignment = Assignment(
                variable=variable,
                timeslot_id=timeslot_id,
                room_id=room_id,
                instructor_id=instructor_id,
                ta_id=ta_id
            )
            
            # Phase 3: Check if assignment is valid
            if self._is_valid(assignment):
                # Make assignment
                self.assignments.append(assignment)
                
                # Recurse
                if self._backtrack(var_index + 1):
                    return True
                
                # Backtrack
                self.assignments.pop()
        
        print(f"DEBUG: All {len(domain)} assignments failed for {variable}")
        return False
    
    def _get_domain(self, var: Variable) -> List[Tuple[int, int, Optional[int], Optional[int]]]:
        """Get all possible (timeslot, room, instructor, ta) combinations for a variable"""
        domain = []
        
        # Get appropriate timeslots based on duration
        if var.duration == 90:
            timeslots = self.db.query(models.TimeSlot).filter(
                models.TimeSlot.duration == 90
            ).all()
        else:  # 45-minute (half tutorials)
            timeslots = self.db.query(models.TimeSlot).filter(
                models.TimeSlot.duration == 45
            ).all()
        
        # Get appropriate rooms based on session type
        if var.session_type == SessionType.LECTURE:
            rooms = self.db.query(models.Room).filter(
                models.Room.room_type.in_(['Hall', 'Theater', 'Classroom'])
            ).all()
        elif var.session_type == SessionType.LAB:
            rooms = self.db.query(models.Room).filter(
                models.Room.room_type.in_(['Lab', 'Drawing Studio'])
            ).all()
        else:  # Tutorial
            rooms = self.db.query(models.Room).filter(
                models.Room.room_type == 'Classroom'
            ).all()
        
        # Get qualified instructors/TAs
        if var.session_type == SessionType.LECTURE:
            instructors = self.db.query(models.Instructor).join(
                models.instructor_qualified_courses
            ).filter(
                models.instructor_qualified_courses.c.course_id == var.course_id
            ).all()
            
            for timeslot in timeslots:
                for room in rooms:
                    for instructor in instructors:
                        domain.append((timeslot.timeslot_id, room.room_id, instructor.instructor_id, None))
        else:  # Lab or Tutorial - use TAs
            tas = self.db.query(models.TA).join(
                models.ta_qualified_courses
            ).filter(
                models.ta_qualified_courses.c.course_id == var.course_id
            ).all()
            
            for timeslot in timeslots:
                for room in rooms:
                    for ta in tas:
                        domain.append((timeslot.timeslot_id, room.room_id, None, ta.ta_id))
        
        return domain
    
    def _is_valid(self, assignment: Assignment) -> bool:
        """Phase 3: Check all hard constraints"""
        var = assignment.variable
        
        # Get entities
        timeslot = self.db.query(models.TimeSlot).get(assignment.timeslot_id)
        room = self.db.query(models.Room).get(assignment.room_id)
        
        # DETAILED DEBUG for Lab (Course 2, Section 28)
        is_target = (var.session_type == SessionType.LAB and 
                     var.section_id == 28)
        
        # Check room capacity
        if var.session_type == SessionType.LECTURE:
            group = self.db.query(models.Group).get(var.group_id)
            if room.capacity < group.num_students:
                if is_target:
                    print(f"DEBUG FAIL: Room capacity {room.capacity} < {group.num_students} students")
                return False
        else:
            section = self.db.query(models.Section).get(var.section_id)
            if room.capacity < section.num_students:
                if is_target:
                    print(f"DEBUG FAIL: Room capacity {room.capacity} < {section.num_students} students (Section {section.section_number})")
                return False
        
        # Check all existing assignments for conflicts
        for existing in self.assignments:
            # Same time check - timeslot_id ALREADY includes day+time
            if existing.timeslot_id == assignment.timeslot_id:
                # Room conflict (same room, same day, same time)
                if existing.room_id == assignment.room_id:
                    if is_target:
                        print(f"DEBUG FAIL: Room {room.room_number} already used at {timeslot.day} {timeslot.start_time} by {existing.variable}")
                    return False
                
                # Instructor/TA conflict (same person, same time)
                if assignment.instructor_id and existing.instructor_id == assignment.instructor_id:
                    if is_target:
                        print(f"DEBUG FAIL: Instructor conflict at {timeslot.day} {timeslot.start_time}")
                    return False
                if assignment.ta_id and existing.ta_id == assignment.ta_id:
                    if is_target:
                        print(f"DEBUG FAIL: TA conflict at {timeslot.day} {timeslot.start_time}")
                    return False
                
                # Hierarchy conflicts (CRITICAL)
                if not self._check_hierarchy_conflict(var, existing.variable):
                    if is_target:
                        print(f"DEBUG FAIL: Hierarchy conflict with {existing.variable} at {timeslot.day} {timeslot.start_time}")
                    return False
        
        if is_target:
            print(f"DEBUG PASS: Lab (Course 2, Section 28) valid at {timeslot.day} {timeslot.start_time} in {room.room_number}")
        return True
    
    def _check_hierarchy_conflict(self, var1: Variable, var2: Variable) -> bool:
        """Check if two variables have a hierarchy conflict (Group/Section relationship)"""
        # Get group and section information
        if var1.session_type == SessionType.LECTURE:
            group1_id = var1.group_id
            sections1 = [s.section_id for s in self.db.query(models.Section).filter(
                models.Section.group_id == group1_id
            ).all()]
        else:
            section1 = self.db.query(models.Section).get(var1.section_id)
            group1_id = section1.group_id if section1 else None
            sections1 = [var1.section_id]
        
        if var2.session_type == SessionType.LECTURE:
            group2_id = var2.group_id
            sections2 = [s.section_id for s in self.db.query(models.Section).filter(
                models.Section.group_id == group2_id
            ).all()]
        else:
            section2 = self.db.query(models.Section).get(var2.section_id)
            group2_id = section2.group_id if section2 else None
            sections2 = [var2.section_id]
        
        # Group Integrity: Same group cannot be in two places
        if var1.session_type == SessionType.LECTURE and var2.session_type == SessionType.LECTURE:
            if group1_id == group2_id:
                return False
        
        # Parent-Child Conflict: If group is busy, sections cannot be busy
        if var1.session_type == SessionType.LECTURE and var2.session_type != SessionType.LECTURE:
            if var2.section_id in sections1:
                return False
        
        if var2.session_type == SessionType.LECTURE and var1.session_type != SessionType.LECTURE:
            if var1.section_id in sections2:
                return False
        
        # Section Integrity: Same section cannot be in two places
        if var1.session_type != SessionType.LECTURE and var2.session_type != SessionType.LECTURE:
            if var1.section_id == var2.section_id:
                return False
        
        return True
    
    def _save_to_database(self):
        """Save all assignments to the database"""
        for assignment in self.assignments:
            var = assignment.variable
            
            if var.session_type == SessionType.LECTURE:
                group = self.db.query(models.Group).get(var.group_id)
                schedule_entry = models.Schedule(
                    course_id=var.course_id,
                    group_id=var.group_id,
                    instructor_id=assignment.instructor_id,
                    room_id=assignment.room_id,
                    timeslot_id=assignment.timeslot_id,
                    session_type='Lecture'
                )
            else:
                section = self.db.query(models.Section).get(var.section_id)
                schedule_entry = models.Schedule(
                    course_id=var.course_id,
                    group_id=section.group_id,
                    ta_id=assignment.ta_id,
                    room_id=assignment.room_id,
                    timeslot_id=assignment.timeslot_id,
                    session_type=var.session_type.value
                )
            
            self.db.add(schedule_entry)
    
    def _schedule_lecture(self, course: models.Course, groups: list) -> bool:
        """Schedule lecture for all groups at the same time"""
        # Get available instructor qualified for this course
        instructor = self.db.query(models.Instructor).join(
            models.instructor_qualified_courses
        ).filter(
            models.instructor_qualified_courses.c.course_id == course.course_id
        ).first()
        
        if not instructor:
            return False
        
        # Get available room (Hall, Theater, or Classroom)
        rooms = self.db.query(models.Room).filter(
            models.Room.room_type.in_(['Hall', 'Theater', 'Classroom'])
        ).all()
        
        if not rooms:
            return False
        
        # Get available 90-minute time slots
        timeslots = self.db.query(models.TimeSlot).filter(
            models.TimeSlot.duration == 90
        ).all()
        
        # Try to find an available slot
        for room in rooms:
            for timeslot in timeslots:
                # Check if room and instructor are available
                conflict = self.db.query(models.Schedule).filter(
                    models.Schedule.timeslot_id == timeslot.timeslot_id,
                    and_(
                        (models.Schedule.room_id == room.room_id) |
                        (models.Schedule.instructor_id == instructor.instructor_id)
                    )
                ).first()
                
                if not conflict:
                    # Schedule lecture for all groups
                    for group in groups:
                        schedule_entry = models.Schedule(
                            course_id=course.course_id,
                            group_id=group.group_id,
                            instructor_id=instructor.instructor_id,
                            room_id=room.room_id,
                            timeslot_id=timeslot.timeslot_id,
                            session_type='Lecture'
                        )
                        self.db.add(schedule_entry)
                    
                    return True
        
        return False
    
    def _schedule_lab(self, course: models.Course, group: models.Group) -> bool:
        """Schedule lab for a specific group"""
        # Get available TA qualified for this course
        ta = self.db.query(models.TA).join(
            models.ta_qualified_courses
        ).filter(
            models.ta_qualified_courses.c.course_id == course.course_id
        ).first()
        
        if not ta:
            return False
        
        # Get available lab rooms
        labs = self.db.query(models.Room).filter(
            models.Room.room_type == 'Lab'
        ).all()
        
        if not labs:
            return False
        
        # Get available 90-minute time slots
        timeslots = self.db.query(models.TimeSlot).filter(
            models.TimeSlot.duration == 90
        ).all()
        
        # Try to find an available slot
        for lab in labs:
            for timeslot in timeslots:
                # Check if lab and TA are available
                conflict = self.db.query(models.Schedule).filter(
                    models.Schedule.timeslot_id == timeslot.timeslot_id,
                    and_(
                        (models.Schedule.room_id == lab.room_id) |
                        (models.Schedule.ta_id == ta.ta_id)
                    )
                ).first()
                
                if not conflict:
                    # Schedule the lab
                    schedule_entry = models.Schedule(
                        course_id=course.course_id,
                        group_id=group.group_id,
                        ta_id=ta.ta_id,
                        room_id=lab.room_id,
                        timeslot_id=timeslot.timeslot_id,
                        session_type='Lab'
                    )
                    self.db.add(schedule_entry)
                    return True
        
        return False
    
    def _schedule_tutorial(self, course: models.Course, group: models.Group) -> bool:
        """Schedule tutorial for a specific group"""
        # Get available TA qualified for this course
        ta = self.db.query(models.TA).join(
            models.ta_qualified_courses
        ).filter(
            models.ta_qualified_courses.c.course_id == course.course_id
        ).first()
        
        if not ta:
            return False
        
        # Get available classrooms/halls
        rooms = self.db.query(models.Room).filter(
            models.Room.room_type.in_(['Classroom', 'Hall'])
        ).all()
        
        if not rooms:
            return False
        
        # Get appropriate time slots based on tutorial_slots duration
        # 0.5 slots = 45 minutes, otherwise 90 minutes
        if course.tutorial_slots == 0.5:
            timeslots = self.db.query(models.TimeSlot).filter(
                models.TimeSlot.duration == 45
            ).all()
        else:
            timeslots = self.db.query(models.TimeSlot).filter(
                models.TimeSlot.duration == 90
            ).all()
        
        # Try to find an available slot
        for room in rooms:
            for timeslot in timeslots:
                # Check if room and TA are available
                conflict = self.db.query(models.Schedule).filter(
                    models.Schedule.timeslot_id == timeslot.timeslot_id,
                    and_(
                        (models.Schedule.room_id == room.room_id) |
                        (models.Schedule.ta_id == ta.ta_id)
                    )
                ).first()
                
                if not conflict:
                    # Schedule the tutorial
                    schedule_entry = models.Schedule(
                        course_id=course.course_id,
                        group_id=group.group_id,
                        ta_id=ta.ta_id,
                        room_id=room.room_id,
                        timeslot_id=timeslot.timeslot_id,
                        session_type='Tutorial'
                    )
                    self.db.add(schedule_entry)
                    return True
        
        return False
