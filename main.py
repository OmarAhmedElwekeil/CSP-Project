import sys
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
                             QTabWidget, QLabel, QLineEdit, QComboBox, QMessageBox,
                             QSpinBox, QCheckBox, QFileDialog, QDialog, QFormLayout,
                             QHeaderView, QTextEdit)
from PyQt5.QtCore import Qt
import pandas as pd
from openpyxl import Workbook


class DatabaseManager:
    def __init__(self, db_name="timetable.db"):
        self.db_name = db_name
        self.conn = None
        self.setup_database()
    
    def get_connection(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_name)
        return self.conn
    
    def setup_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Buildings
        cursor.execute('''CREATE TABLE IF NOT EXISTS Buildings (
            BuildingID INTEGER PRIMARY KEY AUTOINCREMENT,
            BuildingName TEXT NOT NULL UNIQUE
        )''')
        
        # Rooms
        cursor.execute('''CREATE TABLE IF NOT EXISTS Rooms (
            RoomID INTEGER PRIMARY KEY AUTOINCREMENT,
            BuildingID INTEGER NOT NULL,
            RoomNumber TEXT NOT NULL,
            RoomType TEXT NOT NULL,
            Capacity INTEGER NOT NULL,
            FOREIGN KEY (BuildingID) REFERENCES Buildings(BuildingID) ON DELETE CASCADE
        )''')
        
        # Levels
        cursor.execute('''CREATE TABLE IF NOT EXISTS Levels (
            LevelID INTEGER PRIMARY KEY AUTOINCREMENT,
            LevelName TEXT NOT NULL UNIQUE,
            Specialization TEXT,
            NumSections INTEGER NOT NULL,
            NumGroupsPerSection INTEGER NOT NULL,
            TotalStudents INTEGER NOT NULL
        )''')
        
        # Groups
        cursor.execute('''CREATE TABLE IF NOT EXISTS Groups (
            GroupID INTEGER PRIMARY KEY AUTOINCREMENT,
            LevelID INTEGER NOT NULL,
            SectionID INTEGER NOT NULL,
            GroupNumber INTEGER NOT NULL,
            NumStudents INTEGER NOT NULL,
            FOREIGN KEY (LevelID) REFERENCES Levels(LevelID) ON DELETE CASCADE,
            FOREIGN KEY (SectionID) REFERENCES Sections(SectionID) ON DELETE CASCADE
        )''')
        
        # Sections
        cursor.execute('''CREATE TABLE IF NOT EXISTS Sections (
            SectionID INTEGER PRIMARY KEY AUTOINCREMENT,
            LevelID INTEGER NOT NULL,
            SectionNumber INTEGER NOT NULL,
            NumStudents INTEGER NOT NULL,
            FOREIGN KEY (LevelID) REFERENCES Levels(LevelID) ON DELETE CASCADE
        )''')
        
        # Courses
        # Check if we need to update the Courses table structure
        cursor.execute("PRAGMA table_info(Courses)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'NumLectures' in columns:  # Old schema detected
            cursor.execute('DROP TABLE IF EXISTS Courses')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS Courses (
            CourseID INTEGER PRIMARY KEY AUTOINCREMENT,
            CourseCode TEXT NOT NULL UNIQUE,
            CourseName TEXT NOT NULL,
            LevelID INTEGER NOT NULL,
            HasLab INTEGER DEFAULT 0,
            HasTutorial INTEGER DEFAULT 0,
            IsHalfSlot INTEGER DEFAULT 0,
            FOREIGN KEY (LevelID) REFERENCES Levels(LevelID) ON DELETE CASCADE
        )''')
        
        # Instructors
        cursor.execute('''CREATE TABLE IF NOT EXISTS Instructors (
            InstructorID INTEGER PRIMARY KEY AUTOINCREMENT,
            InstructorName TEXT NOT NULL UNIQUE
        )''')
        
        # TAs
        cursor.execute('''CREATE TABLE IF NOT EXISTS TAs (
            TAID INTEGER PRIMARY KEY AUTOINCREMENT,
            TAName TEXT NOT NULL UNIQUE
        )''')
        
        # Instructor_QualifiedCourses
        cursor.execute('''CREATE TABLE IF NOT EXISTS Instructor_QualifiedCourses (
            InstructorID INTEGER NOT NULL,
            CourseID INTEGER NOT NULL,
            PRIMARY KEY (InstructorID, CourseID),
            FOREIGN KEY (InstructorID) REFERENCES Instructors(InstructorID) ON DELETE CASCADE,
            FOREIGN KEY (CourseID) REFERENCES Courses(CourseID) ON DELETE CASCADE
        )''')
        
        # TA_QualifiedCourses
        cursor.execute('''CREATE TABLE IF NOT EXISTS TA_QualifiedCourses (
            TAID INTEGER NOT NULL,
            CourseID INTEGER NOT NULL,
            PRIMARY KEY (TAID, CourseID),
            FOREIGN KEY (TAID) REFERENCES TAs(TAID) ON DELETE CASCADE,
            FOREIGN KEY (CourseID) REFERENCES Courses(CourseID) ON DELETE CASCADE
        )''')
        
        # TimeSlots
        cursor.execute('''CREATE TABLE IF NOT EXISTS TimeSlots (
            TimeSlotID INTEGER PRIMARY KEY AUTOINCREMENT,
            Day TEXT NOT NULL,
            StartTime TEXT NOT NULL,
            EndTime TEXT NOT NULL,
            Duration INTEGER NOT NULL
        )''')
        
        # Schedule
        cursor.execute('''CREATE TABLE IF NOT EXISTS Schedule (
            ScheduleID INTEGER PRIMARY KEY AUTOINCREMENT,
            CourseID INTEGER NOT NULL,
            GroupID INTEGER NOT NULL,
            InstructorID INTEGER,
            TAID INTEGER,
            RoomID INTEGER NOT NULL,
            TimeSlotID INTEGER NOT NULL,
            SessionType TEXT NOT NULL,
            FOREIGN KEY (CourseID) REFERENCES Courses(CourseID) ON DELETE CASCADE,
            FOREIGN KEY (GroupID) REFERENCES Groups(GroupID) ON DELETE CASCADE,
            FOREIGN KEY (InstructorID) REFERENCES Instructors(InstructorID) ON DELETE SET NULL,
            FOREIGN KEY (TAID) REFERENCES TAs(TAID) ON DELETE SET NULL,
            FOREIGN KEY (RoomID) REFERENCES Rooms(RoomID) ON DELETE CASCADE,
            FOREIGN KEY (TimeSlotID) REFERENCES TimeSlots(TimeSlotID) ON DELETE CASCADE
        )''')
        
        # Insert default time slots if empty
        cursor.execute("SELECT COUNT(*) FROM TimeSlots")
        if cursor.fetchone()[0] == 0:
            time_slots = [
                # Sunday
                ('Sunday', '08:30', '10:00', 90),
                ('Sunday', '10:15', '11:45', 90),
                ('Sunday', '12:00', '13:30', 90),
                ('Sunday', '13:45', '15:15', 90),
                ('Sunday', '08:30', '09:15', 45),
                ('Sunday', '09:15', '10:00', 45),
                ('Sunday', '10:15', '11:00', 45),
                ('Sunday', '11:00', '11:45', 45),
                ('Sunday', '12:00', '12:45', 45),
                ('Sunday', '12:45', '13:30', 45),
                ('Sunday', '13:45', '14:30', 45),
                ('Sunday', '14:30', '15:15', 45),
                
                # Monday
                ('Monday', '08:30', '10:00', 90),
                ('Monday', '10:15', '11:45', 90),
                ('Monday', '12:00', '13:30', 90),
                ('Monday', '13:45', '15:15', 90),
                ('Monday', '08:30', '09:15', 45),
                ('Monday', '09:15', '10:00', 45),
                ('Monday', '10:15', '11:00', 45),
                ('Monday', '11:00', '11:45', 45),
                ('Monday', '12:00', '12:45', 45),
                ('Monday', '12:45', '13:30', 45),
                ('Monday', '13:45', '14:30', 45),
                ('Monday', '14:30', '15:15', 45),
                # Tuesday
                ('Tuesday', '08:30', '10:00', 90),
                ('Tuesday', '10:15', '11:45', 90),
                ('Tuesday', '12:00', '13:30', 90),
                ('Tuesday', '13:45', '15:15', 90),
                ('Tuesday', '08:30', '09:15', 45),
                ('Tuesday', '09:15', '10:00', 45),
                ('Tuesday', '10:15', '11:00', 45),
                ('Tuesday', '11:00', '11:45', 45),
                ('Tuesday', '12:00', '12:45', 45),
                ('Tuesday', '12:45', '13:30', 45),
                ('Tuesday', '13:45', '14:30', 45),
                ('Tuesday', '14:30', '15:15', 45),
                
                # Wednesday
                ('Wednesday', '08:30', '10:00', 90),
                ('Wednesday', '10:15', '11:45', 90),
                ('Wednesday', '12:00', '13:30', 90),
                ('Wednesday', '13:45', '15:15', 90),
                ('Wednesday', '08:30', '09:15', 45),
                ('Wednesday', '09:15', '10:00', 45),
                ('Wednesday', '10:15', '11:00', 45),
                ('Wednesday', '11:00', '11:45', 45),
                ('Wednesday', '12:00', '12:45', 45),
                ('Wednesday', '12:45', '13:30', 45),
                ('Wednesday', '13:45', '14:30', 45),
                ('Wednesday', '14:30', '15:15', 45),
                
                # Thursday
                ('Thursday', '08:30', '10:00', 90),
                ('Thursday', '10:15', '11:45', 90),
                ('Thursday', '12:00', '13:30', 90),
                ('Thursday', '13:45', '15:15', 90),
                ('Thursday', '08:30', '09:15', 45),
                ('Thursday', '09:15', '10:00', 45),
                ('Thursday', '10:15', '11:00', 45),
                ('Thursday', '11:00', '11:45', 45),
                ('Thursday', '12:00', '12:45', 45),
                ('Thursday', '12:45', '13:30', 45),
                ('Thursday', '13:45', '14:30', 45),
                ('Thursday', '14:30', '15:15', 45),
            ]
            cursor.executemany("INSERT INTO TimeSlots (Day, StartTime, EndTime, Duration) VALUES (?, ?, ?, ?)", 
                             time_slots)
        
        conn.commit()
    
    def clear_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        tables = ['Schedule', 'TA_QualifiedCourses', 'Instructor_QualifiedCourses', 
                  'Courses', 'Groups', 'Sections', 'Levels', 'Rooms', 'Buildings', 
                  'TAs', 'Instructors']
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
        conn.commit()


class CSPScheduler:
    def __init__(self, db):
        self.db = db

    def generate_schedule(self):
        try:
            # Clear existing schedule
            cursor = self.db.get_connection().cursor()
            cursor.execute("DELETE FROM Schedule")
            self.db.get_connection().commit()

            # Get all courses
            cursor.execute("""
                SELECT CourseID, LevelID, HasLab, HasTutorial, IsHalfSlot
                FROM Courses
            """)
            courses = cursor.fetchall()

            if not courses:
                return False, "No courses found to schedule"

            # Schedule each course
            for course in courses:
                course_id, level_id, has_lab, has_tutorial, is_half_slot = course
                
                # Get all groups for this level, grouped by section
                cursor.execute("""
                    SELECT SectionID, GROUP_CONCAT(GroupID) as GroupIDs
                    FROM Groups
                    WHERE LevelID = ?
                    GROUP BY SectionID
                """, (level_id,))
                sections = cursor.fetchall()

                if not sections:
                    continue

                # Schedule lecture - same time for all groups in a section
                # Get available instructor
                cursor.execute("""
                    SELECT InstructorID 
                    FROM Instructor_QualifiedCourses 
                    WHERE CourseID = ? 
                    LIMIT 1
                """, (course_id,))
                instructor = cursor.fetchone()
                
                if instructor:
                    instructor_id = instructor[0]
                    # Get available room
                    cursor.execute("""
                        SELECT RoomID 
                        FROM Rooms 
                        WHERE RoomType IN ('Hall', 'Theater', 'Classroom')
                        LIMIT 1
                    """)
                    room = cursor.fetchone()
                    
                    if room:
                        room_id = room[0]
                        # Get available time slot
                        cursor.execute("""
                            SELECT TimeSlotID 
                            FROM TimeSlots 
                            WHERE NOT EXISTS (
                                SELECT 1 FROM Schedule 
                                WHERE Schedule.TimeSlotID = TimeSlots.TimeSlotID 
                                AND (Schedule.RoomID = ? OR Schedule.InstructorID = ?)
                            )
                            LIMIT 1
                        """, (room_id, instructor_id))
                        time_slot = cursor.fetchone()
                        
                        if time_slot:
                            time_slot_id = time_slot[0]
                            # Schedule the lecture for all groups in all sections
                            for section in sections:
                                group_ids = section[1].split(',')
                                for group_id in group_ids:
                                    cursor.execute("""
                                        INSERT INTO Schedule 
                                        (CourseID, GroupID, InstructorID, RoomID, TimeSlotID, SessionType)
                                        VALUES (?, ?, ?, ?, ?, 'Lecture')
                                    """, (course_id, group_id, instructor_id, room_id, time_slot_id))

                # Schedule labs and tutorials separately for each group
                for section in sections:
                    group_ids = section[1].split(',')
                    for group_id in group_ids:
                        # Schedule lab if needed
                        if has_lab:
                            # Get available TA
                            cursor.execute("""
                                SELECT TAID 
                                FROM TA_QualifiedCourses 
                                WHERE CourseID = ? 
                                LIMIT 1
                            """, (course_id,))
                            ta = cursor.fetchone()
                            
                            if ta:
                                ta_id = ta[0]
                                # Get available lab
                                cursor.execute("""
                                    SELECT RoomID 
                                    FROM Rooms 
                                    WHERE RoomType = 'Lab'
                                    LIMIT 1
                                """)
                                lab = cursor.fetchone()
                                
                                if lab:
                                    lab_id = lab[0]
                                    # Get available time slot
                                    cursor.execute("""
                                        SELECT TimeSlotID 
                                        FROM TimeSlots 
                                        WHERE NOT EXISTS (
                                            SELECT 1 FROM Schedule 
                                            WHERE Schedule.TimeSlotID = TimeSlots.TimeSlotID 
                                            AND (Schedule.RoomID = ? OR Schedule.TAID = ?)
                                        )
                                        LIMIT 1
                                    """, (lab_id, ta_id))
                                    time_slot = cursor.fetchone()
                                    
                                    if time_slot:
                                        # Schedule the lab
                                        cursor.execute("""
                                            INSERT INTO Schedule 
                                            (CourseID, GroupID, TAID, RoomID, TimeSlotID, SessionType)
                                            VALUES (?, ?, ?, ?, ?, 'Lab')
                                        """, (course_id, group_id, ta_id, lab_id, time_slot[0]))

                        # Schedule tutorial if needed
                        if has_tutorial:
                            # Get available TA
                            cursor.execute("""
                                SELECT TAID 
                                FROM TA_QualifiedCourses 
                                WHERE CourseID = ? 
                                LIMIT 1
                            """, (course_id,))
                            ta = cursor.fetchone()
                            
                            if ta:
                                ta_id = ta[0]
                                # Get available room
                                cursor.execute("""
                                    SELECT RoomID 
                                    FROM Rooms 
                                    WHERE RoomType IN ('Classroom', 'Hall')
                                    LIMIT 1
                                """)
                                room = cursor.fetchone()
                                
                                if room:
                                    room_id = room[0]
                                    # Get available time slot
                                    cursor.execute("""
                                        SELECT TimeSlotID 
                                        FROM TimeSlots 
                                        WHERE NOT EXISTS (
                                            SELECT 1 FROM Schedule 
                                            WHERE Schedule.TimeSlotID = TimeSlots.TimeSlotID 
                                            AND (Schedule.RoomID = ? OR Schedule.TAID = ?)
                                        )
                                        LIMIT 1
                                    """, (room_id, ta_id))
                                    time_slot = cursor.fetchone()
                                    
                                    if time_slot:
                                        # Schedule the tutorial
                                        cursor.execute("""
                                            INSERT INTO Schedule 
                                            (CourseID, GroupID, TAID, RoomID, TimeSlotID, SessionType)
                                            VALUES (?, ?, ?, ?, ?, 'Tutorial')
                                        """, (course_id, group_id, ta_id, room_id, time_slot[0]))

            self.db.get_connection().commit()
            return True, "Schedule generated successfully"
        except Exception as e:
            return False, str(e)

class TimetableApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.scheduler = CSPScheduler(self.db)
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("University Timetable Scheduling System")
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Create tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Add tabs
        self.tabs.addTab(self.create_buildings_tab(), "Buildings")
        self.tabs.addTab(self.create_rooms_tab(), "Rooms")
        self.tabs.addTab(self.create_levels_tab(), "Levels")
        self.tabs.addTab(self.create_courses_tab(), "Courses")
        self.tabs.addTab(self.create_instructors_tab(), "Instructors")
        self.tabs.addTab(self.create_tas_tab(), "TAs")
        self.tabs.addTab(self.create_schedule_tab(), "Schedule")
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        generate_btn = QPushButton("Generate Schedule")
        generate_btn.clicked.connect(self.generate_schedule)
        button_layout.addWidget(generate_btn)
        
        export_btn = QPushButton("Export to Excel")
        export_btn.clicked.connect(self.export_to_excel)
        button_layout.addWidget(export_btn)
        
        import_btn = QPushButton("Import from Excel")
        import_btn.clicked.connect(self.import_from_excel)
        button_layout.addWidget(import_btn)
        
        clear_btn = QPushButton("Clear Database")
        clear_btn.clicked.connect(self.clear_database)
        button_layout.addWidget(clear_btn)
        
        layout.addLayout(button_layout)
        
        self.show()
    
    def create_buildings_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Form
        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel("Building Name:"))
        self.building_name_input = QLineEdit()
        form_layout.addWidget(self.building_name_input)
        
        add_btn = QPushButton("Add Building")
        add_btn.clicked.connect(self.add_building)
        form_layout.addWidget(add_btn)
        
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_building)
        form_layout.addWidget(delete_btn)
        
        layout.addLayout(form_layout)
        
        # Table
        self.buildings_table = QTableWidget()
        self.buildings_table.setColumnCount(2)
        self.buildings_table.setHorizontalHeaderLabels(["BuildingID", "BuildingName"])
        self.buildings_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.buildings_table)
        
        widget.setLayout(layout)
        self.refresh_buildings_table()
        return widget
    
    def add_building(self):
        name = self.building_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Building name cannot be empty")
            return
        
        try:
            cursor = self.db.get_connection().cursor()
            cursor.execute("INSERT INTO Buildings (BuildingName) VALUES (?)", (name,))
            self.db.get_connection().commit()
            self.building_name_input.clear()
            self.refresh_buildings_table()
            QMessageBox.information(self, "Success", "Building added successfully")
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "Building already exists")
    
    def delete_building(self):
        row = self.buildings_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Please select a building to delete")
            return
        
        building_id = int(self.buildings_table.item(row, 0).text())
        cursor = self.db.get_connection().cursor()
        cursor.execute("DELETE FROM Buildings WHERE BuildingID = ?", (building_id,))
        self.db.get_connection().commit()
        self.refresh_buildings_table()
        self.refresh_rooms_table()
        QMessageBox.information(self, "Success", "Building deleted successfully")
    
    def refresh_buildings_table(self):
        cursor = self.db.get_connection().cursor()
        cursor.execute("SELECT BuildingID, BuildingName FROM Buildings ORDER BY BuildingID")
        buildings = cursor.fetchall()
        
        self.buildings_table.setRowCount(len(buildings))
        for i, building in enumerate(buildings):
            self.buildings_table.setItem(i, 0, QTableWidgetItem(str(building[0])))
            self.buildings_table.setItem(i, 1, QTableWidgetItem(building[1]))
    
    def create_rooms_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Form
        form_layout = QHBoxLayout()
        
        form_layout.addWidget(QLabel("Building:"))
        self.room_building_combo = QComboBox()
        form_layout.addWidget(self.room_building_combo)
        
        form_layout.addWidget(QLabel("Room Number:"))
        self.room_number_input = QLineEdit()
        form_layout.addWidget(self.room_number_input)
        
        form_layout.addWidget(QLabel("Type:"))
        self.room_type_combo = QComboBox()
        self.room_type_combo.addItems(["Hall", "Theater", "Classroom", "Lab", "Drawing Studio"])
        form_layout.addWidget(self.room_type_combo)
        
        form_layout.addWidget(QLabel("Capacity:"))
        self.room_capacity_input = QSpinBox()
        self.room_capacity_input.setRange(1, 500)
        self.room_capacity_input.setValue(30)
        form_layout.addWidget(self.room_capacity_input)
        
        add_btn = QPushButton("Add Room")
        add_btn.clicked.connect(self.add_room)
        form_layout.addWidget(add_btn)
        
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_room)
        form_layout.addWidget(delete_btn)
        
        layout.addLayout(form_layout)
        
        # Table
        self.rooms_table = QTableWidget()
        self.rooms_table.setColumnCount(5)
        self.rooms_table.setHorizontalHeaderLabels(["RoomID", "Building", "RoomNumber", "Type", "Capacity"])
        self.rooms_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.rooms_table)
        
        widget.setLayout(layout)
        self.refresh_room_combo()
        self.refresh_rooms_table()
        return widget
    
    def refresh_room_combo(self):
        self.room_building_combo.clear()
        cursor = self.db.get_connection().cursor()
        cursor.execute("SELECT BuildingID, BuildingName FROM Buildings ORDER BY BuildingID")
        buildings = cursor.fetchall()
        for building in buildings:
            self.room_building_combo.addItem(building[1], building[0])
    
    def add_room(self):
        if self.room_building_combo.count() == 0:
            QMessageBox.warning(self, "Error", "Please add a building first")
            return
        
        building_id = self.room_building_combo.currentData()
        room_number = self.room_number_input.text().strip()
        room_type = self.room_type_combo.currentText()
        capacity = self.room_capacity_input.value()
        
        if not room_number:
            QMessageBox.warning(self, "Error", "Room number cannot be empty")
            return
        
        cursor = self.db.get_connection().cursor()
        cursor.execute("INSERT INTO Rooms (BuildingID, RoomNumber, RoomType, Capacity) VALUES (?, ?, ?, ?)",
                      (building_id, room_number, room_type, capacity))
        self.db.get_connection().commit()
        self.room_number_input.clear()
        self.refresh_rooms_table()
        QMessageBox.information(self, "Success", "Room added successfully")
    
    def delete_room(self):
        row = self.rooms_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Please select a room to delete")
            return
        
        room_id = int(self.rooms_table.item(row, 0).text())
        cursor = self.db.get_connection().cursor()
        cursor.execute("DELETE FROM Rooms WHERE RoomID = ?", (room_id,))
        self.db.get_connection().commit()
        self.refresh_rooms_table()
        QMessageBox.information(self, "Success", "Room deleted successfully")
    
    def refresh_rooms_table(self):
        cursor = self.db.get_connection().cursor()
        cursor.execute("""
            SELECT r.RoomID, b.BuildingName, r.RoomNumber, r.RoomType, r.Capacity
            FROM Rooms r
            JOIN Buildings b ON r.BuildingID = b.BuildingID
            ORDER BY r.RoomID
        """)
        rooms = cursor.fetchall()
        
        self.rooms_table.setRowCount(len(rooms))
        for i, room in enumerate(rooms):
            for j, value in enumerate(room):
                self.rooms_table.setItem(i, j, QTableWidgetItem(str(value)))
    
    def create_levels_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Form
        form_layout = QHBoxLayout()
        
        form_layout.addWidget(QLabel("Level:"))
        self.level_number_combo = QComboBox()
        self.level_number_combo.addItems(["Level 1", "Level 2", "Level 3", "Level 4"])
        self.level_number_combo.currentTextChanged.connect(self.on_level_number_changed)
        form_layout.addWidget(self.level_number_combo)
        
        form_layout.addWidget(QLabel("Specialization:"))
        self.level_spec_input = QLineEdit()
        self.level_spec_input.setEnabled(False)
        form_layout.addWidget(self.level_spec_input)
        
        form_layout.addWidget(QLabel("Sections:"))
        self.level_sections_input = QSpinBox()
        self.level_sections_input.setRange(1, 10)  # Max 10 sections
        self.level_sections_input.setValue(1)
        form_layout.addWidget(self.level_sections_input)
        
        form_layout.addWidget(QLabel("Groups/Section:"))
        self.level_groups_input = QSpinBox()
        self.level_groups_input.setRange(1, 10)
        self.level_groups_input.setValue(1)
        form_layout.addWidget(self.level_groups_input)
        
        form_layout.addWidget(QLabel("Total Students:"))
        self.level_students_input = QSpinBox()
        self.level_students_input.setRange(1, 1000)
        self.level_students_input.setValue(30)
        form_layout.addWidget(self.level_students_input)
        
        add_btn = QPushButton("Add Level")
        add_btn.clicked.connect(self.add_level)
        form_layout.addWidget(add_btn)
        
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_level)
        form_layout.addWidget(delete_btn)
        
        layout.addLayout(form_layout)
        
        # Note for Level 1 and 2
        note_label = QLabel("Note: Level 1 and 2 contain all students (no specialization). Level 3 and 4 require specialization.")
        note_label.setStyleSheet("color: blue; font-style: italic;")
        layout.addWidget(note_label)
        
        # Table
        self.levels_table = QTableWidget()
        self.levels_table.setColumnCount(6)
        self.levels_table.setHorizontalHeaderLabels(["LevelID", "Name", "Specialization", "Sections", "Groups/Section", "Total Students"])
        self.levels_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.levels_table)
        
        widget.setLayout(layout)
        self.refresh_levels_table()
        return widget
    
    def on_level_number_changed(self):
        level = self.level_number_combo.currentText()
        # Enable specialization input only for Level 3 and 4
        if level in ["Level 3", "Level 4"]:
            self.level_spec_input.setEnabled(True)
            self.level_spec_input.setPlaceholderText("Enter specialization (e.g., AI, CS, Bioinformatics)")
        else:
            self.level_spec_input.setEnabled(False)
            self.level_spec_input.clear()
            self.level_spec_input.setPlaceholderText("Not required for Level 1 and 2")
    
    def add_level(self):
        level_name = self.level_number_combo.currentText()
        spec = self.level_spec_input.text().strip()
        num_sections = self.level_sections_input.value()
        num_groups = self.level_groups_input.value()
        total_students = self.level_students_input.value()
        
        # Validate specialization for Level 3 and 4
        if level_name in ["Level 3", "Level 4"]:
            if not spec:
                QMessageBox.warning(self, "Error", "Specialization is required for Level 3 and Level 4")
                return
            # Create unique level name with specialization
            full_level_name = f"{level_name} - {spec}"
        else:
            # For Level 1 and 2, no specialization
            full_level_name = level_name
            spec = None
        
        try:
            cursor = self.db.get_connection().cursor()
            cursor.execute("""
                INSERT INTO Levels (LevelName, Specialization, NumSections, NumGroupsPerSection, TotalStudents)
                VALUES (?, ?, ?, ?, ?)
            """, (full_level_name, spec, num_sections, num_groups, total_students))
            level_id = cursor.lastrowid
            
            # Create sections and groups
            students_per_section = total_students // num_sections
            students_per_group = students_per_section // num_groups
            
            for section_num in range(1, num_sections + 1):
                cursor.execute("""
                    INSERT INTO Sections (LevelID, SectionNumber, NumStudents)
                    VALUES (?, ?, ?)
                """, (level_id, section_num, students_per_section))
                section_id = cursor.lastrowid
                
                for group_num in range(1, num_groups + 1):
                    cursor.execute("""
                        INSERT INTO Groups (LevelID, SectionID, GroupNumber, NumStudents)
                        VALUES (?, ?, ?, ?)
                    """, (level_id, section_id, group_num, students_per_group))
            
            self.db.get_connection().commit()
            self.level_spec_input.clear()
            self.refresh_levels_table()
            self.refresh_course_combo()
            QMessageBox.information(self, "Success", f"{full_level_name} added with {num_sections} sections and {num_groups} groups per section")
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "This level/specialization combination already exists")
    
    def delete_level(self):
        row = self.levels_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Please select a level to delete")
            return
        
        level_id = int(self.levels_table.item(row, 0).text())
        cursor = self.db.get_connection().cursor()
        cursor.execute("DELETE FROM Levels WHERE LevelID = ?", (level_id,))
        self.db.get_connection().commit()
        self.refresh_levels_table()
        self.refresh_course_combo()
        QMessageBox.information(self, "Success", "Level and related data deleted successfully")
    
    def refresh_levels_table(self):
        cursor = self.db.get_connection().cursor()
        cursor.execute("""
            SELECT LevelID, LevelName, Specialization, NumSections, NumGroupsPerSection, TotalStudents
            FROM Levels ORDER BY LevelID
        """)
        levels = cursor.fetchall()
        
        self.levels_table.setRowCount(len(levels))
        for i, level in enumerate(levels):
            for j, value in enumerate(level):
                self.levels_table.setItem(i, j, QTableWidgetItem(str(value) if value else ""))
    
    def create_courses_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Form
        form_layout = QVBoxLayout()
        
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Course Code:"))
        self.course_code_input = QLineEdit()
        row1.addWidget(self.course_code_input)
        
        row1.addWidget(QLabel("Course Name:"))
        self.course_name_input = QLineEdit()
        row1.addWidget(self.course_name_input)
        
        row1.addWidget(QLabel("Level:"))
        self.course_level_combo = QComboBox()
        row1.addWidget(self.course_level_combo)
        
        form_layout.addLayout(row1)
        
        row2 = QHBoxLayout()
        self.course_has_lab = QCheckBox("Has Lab")
        row2.addWidget(self.course_has_lab)
        
        self.course_has_tutorial = QCheckBox("Has Tutorial")
        row2.addWidget(self.course_has_tutorial)
        
        self.tutorial_half_slot = QCheckBox("Half Slot Tutorial")
        self.tutorial_half_slot.setEnabled(False)
        row2.addWidget(self.tutorial_half_slot)
        
        # Connect tutorial checkbox to enable/disable half slot option
        self.course_has_tutorial.stateChanged.connect(
            lambda state: self.tutorial_half_slot.setEnabled(state == Qt.Checked))
        
        form_layout.addLayout(row2)
        
        row3 = QHBoxLayout()
        add_btn = QPushButton("Add Course")
        add_btn.clicked.connect(self.add_course)
        row3.addWidget(add_btn)
        
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_course)
        row3.addWidget(delete_btn)
        
        assign_instructor_btn = QPushButton("Assign Instructor")
        assign_instructor_btn.clicked.connect(self.assign_instructor_to_course)
        row3.addWidget(assign_instructor_btn)
        
        assign_ta_btn = QPushButton("Assign TA")
        assign_ta_btn.clicked.connect(self.assign_ta_to_course)
        row3.addWidget(assign_ta_btn)
        
        form_layout.addLayout(row3)
        
        layout.addLayout(form_layout)
        
        # Table
        self.courses_table = QTableWidget()
        self.courses_table.setColumnCount(6)
        self.courses_table.setHorizontalHeaderLabels(["CourseID", "Code", "Name", "Level", "Has Lab", "Tutorial Type"])
        self.courses_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.courses_table)
        
        widget.setLayout(layout)
        self.refresh_course_combo()
        self.refresh_courses_table()
        return widget
    
    def refresh_course_combo(self):
        self.course_level_combo.clear()
        cursor = self.db.get_connection().cursor()
        cursor.execute("SELECT LevelID, LevelName FROM Levels ORDER BY LevelID")
        levels = cursor.fetchall()
        for level in levels:
            self.course_level_combo.addItem(level[1], level[0])
    
    def add_course(self):
        if self.course_level_combo.count() == 0:
            QMessageBox.warning(self, "Error", "Please add a level first")
            return
        
        code = self.course_code_input.text().strip()
        name = self.course_name_input.text().strip()
        level_id = self.course_level_combo.currentData()
        has_lab = 1 if self.course_has_lab.isChecked() else 0
        has_tutorial = 1 if self.course_has_tutorial.isChecked() else 0
        is_half_slot = 1 if self.tutorial_half_slot.isChecked() and has_tutorial else 0
        
        if not code or not name:
            QMessageBox.warning(self, "Error", "Course code and name cannot be empty")
            return
            
        # Get the number of groups for the selected level
        cursor = self.db.get_connection().cursor()
        cursor.execute("""
            SELECT NumSections, NumGroupsPerSection 
            FROM Levels 
            WHERE LevelID = ?
        """, (level_id,))
        level_info = cursor.fetchone()
        if not level_info:
            QMessageBox.warning(self, "Error", "Invalid level selected")
            return
            
        num_sections, groups_per_section = level_info
        
        try:
            cursor.execute("""
                INSERT INTO Courses (CourseCode, CourseName, LevelID, HasLab, HasTutorial, IsHalfSlot)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (code, name, level_id, has_lab, has_tutorial, is_half_slot))
            self.db.get_connection().commit()
            self.course_code_input.clear()
            self.course_name_input.clear()
            self.refresh_courses_table()
            QMessageBox.information(self, "Success", "Course added successfully")
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "Course code already exists")
    
    def delete_course(self):
        row = self.courses_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Please select a course to delete")
            return
        
        course_id = int(self.courses_table.item(row, 0).text())
        cursor = self.db.get_connection().cursor()
        cursor.execute("DELETE FROM Courses WHERE CourseID = ?", (course_id,))
        self.db.get_connection().commit()
        self.refresh_courses_table()
        QMessageBox.information(self, "Success", "Course deleted successfully")
    
    def assign_instructor_to_course(self):
        row = self.courses_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Please select a course first")
            return
        
        course_id = int(self.courses_table.item(row, 0).text())
        
        # Get all instructors
        cursor = self.db.get_connection().cursor()
        cursor.execute("SELECT InstructorID, InstructorName FROM Instructors ORDER BY InstructorID")
        instructors = cursor.fetchall()
        
        if not instructors:
            QMessageBox.warning(self, "Error", "No instructors available")
            return
        
        # Create selection dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Assign Instructor")
        layout = QVBoxLayout()
        
        combo = QComboBox()
        for inst in instructors:
            combo.addItem(inst[1], inst[0])
        layout.addWidget(combo)
        
        btn = QPushButton("Assign")
        btn.clicked.connect(lambda: self.perform_instructor_assignment(course_id, combo.currentData(), dialog))
        layout.addWidget(btn)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def perform_instructor_assignment(self, course_id, instructor_id, dialog):
        try:
            cursor = self.db.get_connection().cursor()
            cursor.execute("INSERT INTO Instructor_QualifiedCourses (InstructorID, CourseID) VALUES (?, ?)",
                          (instructor_id, course_id))
            self.db.get_connection().commit()
            QMessageBox.information(self, "Success", "Instructor assigned successfully")
            dialog.close()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "Instructor already assigned to this course")
    
    def assign_ta_to_course(self):
        row = self.courses_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Please select a course first")
            return
        
        course_id = int(self.courses_table.item(row, 0).text())
        
        # Get all TAs
        cursor = self.db.get_connection().cursor()
        cursor.execute("SELECT TAID, TAName FROM TAs ORDER BY TAID")
        tas = cursor.fetchall()
        
        if not tas:
            QMessageBox.warning(self, "Error", "No TAs available")
            return
        
        # Create selection dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Assign TA")
        layout = QVBoxLayout()
        
        combo = QComboBox()
        for ta in tas:
            combo.addItem(ta[1], ta[0])
        layout.addWidget(combo)
        
        btn = QPushButton("Assign")
        btn.clicked.connect(lambda: self.perform_ta_assignment(course_id, combo.currentData(), dialog))
        layout.addWidget(btn)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def perform_ta_assignment(self, course_id, ta_id, dialog):
        try:
            cursor = self.db.get_connection().cursor()
            cursor.execute("INSERT INTO TA_QualifiedCourses (TAID, CourseID) VALUES (?, ?)",
                          (ta_id, course_id))
            self.db.get_connection().commit()
            QMessageBox.information(self, "Success", "TA assigned successfully")
            dialog.close()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "TA already assigned to this course")
    
    def refresh_courses_table(self):
        cursor = self.db.get_connection().cursor()
        cursor.execute("""
            SELECT c.CourseID, c.CourseCode, c.CourseName, l.LevelName, 
                   CASE WHEN c.HasLab = 1 THEN 'Yes' ELSE 'No' END,
                   CASE 
                       WHEN c.HasTutorial = 0 THEN 'None'
                       WHEN c.IsHalfSlot = 1 THEN 'Half Slot'
                       ELSE 'Full Slot'
                   END
            FROM Courses c
            JOIN Levels l ON c.LevelID = l.LevelID
            ORDER BY c.CourseID
        """)
        courses = cursor.fetchall()
        
        self.courses_table.setRowCount(len(courses))
        for i, course in enumerate(courses):
            for j, value in enumerate(course):
                self.courses_table.setItem(i, j, QTableWidgetItem(str(value)))
    
    def create_instructors_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Form
        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel("Instructor Name:"))
        self.instructor_name_input = QLineEdit()
        form_layout.addWidget(self.instructor_name_input)
        
        add_btn = QPushButton("Add Instructor")
        add_btn.clicked.connect(self.add_instructor)
        form_layout.addWidget(add_btn)
        
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_instructor)
        form_layout.addWidget(delete_btn)
        
        layout.addLayout(form_layout)
        
        # Table
        self.instructors_table = QTableWidget()
        self.instructors_table.setColumnCount(2)
        self.instructors_table.setHorizontalHeaderLabels(["InstructorID", "InstructorName"])
        self.instructors_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.instructors_table)
        
        widget.setLayout(layout)
        self.refresh_instructors_table()
        return widget
    
    def add_instructor(self):
        name = self.instructor_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Instructor name cannot be empty")
            return
        
        try:
            cursor = self.db.get_connection().cursor()
            cursor.execute("INSERT INTO Instructors (InstructorName) VALUES (?)", (name,))
            self.db.get_connection().commit()
            self.instructor_name_input.clear()
            self.refresh_instructors_table()
            QMessageBox.information(self, "Success", "Instructor added successfully")
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "Instructor already exists")
    
    def delete_instructor(self):
        row = self.instructors_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Please select an instructor to delete")
            return
        
        instructor_id = int(self.instructors_table.item(row, 0).text())
        cursor = self.db.get_connection().cursor()
        cursor.execute("DELETE FROM Instructors WHERE InstructorID = ?", (instructor_id,))
        self.db.get_connection().commit()
        self.refresh_instructors_table()
        QMessageBox.information(self, "Success", "Instructor deleted successfully")
    
    def refresh_instructors_table(self):
        cursor = self.db.get_connection().cursor()
        cursor.execute("SELECT InstructorID, InstructorName FROM Instructors ORDER BY InstructorID")
        instructors = cursor.fetchall()
        
        self.instructors_table.setRowCount(len(instructors))
        for i, instructor in enumerate(instructors):
            self.instructors_table.setItem(i, 0, QTableWidgetItem(str(instructor[0])))
            self.instructors_table.setItem(i, 1, QTableWidgetItem(instructor[1]))
    
    def create_tas_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Form
        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel("TA Name:"))
        self.ta_name_input = QLineEdit()
        form_layout.addWidget(self.ta_name_input)
        
        add_btn = QPushButton("Add TA")
        add_btn.clicked.connect(self.add_ta)
        form_layout.addWidget(add_btn)
        
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_ta)
        form_layout.addWidget(delete_btn)
        
        layout.addLayout(form_layout)
        
        # Table
        self.tas_table = QTableWidget()
        self.tas_table.setColumnCount(2)
        self.tas_table.setHorizontalHeaderLabels(["TAID", "TAName"])
        self.tas_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.tas_table)
        
        widget.setLayout(layout)
        self.refresh_tas_table()
        return widget
    
    def add_ta(self):
        name = self.ta_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "TA name cannot be empty")
            return
        
        try:
            cursor = self.db.get_connection().cursor()
            cursor.execute("INSERT INTO TAs (TAName) VALUES (?)", (name,))
            self.db.get_connection().commit()
            self.ta_name_input.clear()
            self.refresh_tas_table()
            QMessageBox.information(self, "Success", "TA added successfully")
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "TA already exists")
    
    def delete_ta(self):
        row = self.tas_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Please select a TA to delete")
            return
        
        ta_id = int(self.tas_table.item(row, 0).text())
        cursor = self.db.get_connection().cursor()
        cursor.execute("DELETE FROM TAs WHERE TAID = ?", (ta_id,))
        self.db.get_connection().commit()
        self.refresh_tas_table()
        QMessageBox.information(self, "Success", "TA deleted successfully")
    
    def refresh_tas_table(self):
        cursor = self.db.get_connection().cursor()
        cursor.execute("SELECT TAID, TAName FROM TAs ORDER BY TAID")
        tas = cursor.fetchall()
        
        self.tas_table.setRowCount(len(tas))
        for i, ta in enumerate(tas):
            self.tas_table.setItem(i, 0, QTableWidgetItem(str(ta[0])))
            self.tas_table.setItem(i, 1, QTableWidgetItem(ta[1]))
    
    def create_schedule_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Filter options
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("View by:"))
        
        self.schedule_filter_combo = QComboBox()
        self.schedule_filter_combo.addItems(["All", "Day", "Instructor", "TA", "Course", "Group", "Room"])
        self.schedule_filter_combo.currentTextChanged.connect(self.on_schedule_filter_changed)
        filter_layout.addWidget(self.schedule_filter_combo)
        
        self.schedule_value_combo = QComboBox()
        filter_layout.addWidget(self.schedule_value_combo)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_schedule_table)
        filter_layout.addWidget(refresh_btn)
        
        layout.addLayout(filter_layout)
        
        # Table
        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(12)
        self.schedule_table.setHorizontalHeaderLabels([
            "Day", "Start Time", "End Time", "Course Code", "Course Name", 
            "Instructor/TA", "Room", "Building", "Level", "Section", "Group", "Session Type"
        ])
        self.schedule_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.schedule_table)
        
        widget.setLayout(layout)
        self.on_schedule_filter_changed()
        return widget
    
    def on_schedule_filter_changed(self):
        filter_type = self.schedule_filter_combo.currentText()
        self.schedule_value_combo.clear()
        
        cursor = self.db.get_connection().cursor()
        
        if filter_type == "Day":
            self.schedule_value_combo.addItems(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        elif filter_type == "Instructor":
            cursor.execute("SELECT InstructorID, InstructorName FROM Instructors ORDER BY InstructorID")
            for row in cursor.fetchall():
                self.schedule_value_combo.addItem(row[1], row[0])
        elif filter_type == "TA":
            cursor.execute("SELECT TAID, TAName FROM TAs ORDER BY TAID")
            for row in cursor.fetchall():
                self.schedule_value_combo.addItem(row[1], row[0])
        elif filter_type == "Course":
            cursor.execute("SELECT CourseID, CourseCode FROM Courses ORDER BY CourseID")
            for row in cursor.fetchall():
                self.schedule_value_combo.addItem(row[1], row[0])
        elif filter_type == "Group":
            cursor.execute("""
                SELECT g.GroupID, l.LevelName || ' - Section ' || g.SectionID || ' - Group ' || g.GroupNumber
                FROM Groups g
                JOIN Levels l ON g.LevelID = l.LevelID
                ORDER BY g.GroupID
            """)
            for row in cursor.fetchall():
                self.schedule_value_combo.addItem(row[1], row[0])
        elif filter_type == "Room":
            cursor.execute("""
                SELECT r.RoomID, b.BuildingName || ' - ' || r.RoomNumber
                FROM Rooms r
                JOIN Buildings b ON r.BuildingID = b.BuildingID
                ORDER BY r.RoomID
            """)
            for row in cursor.fetchall():
                self.schedule_value_combo.addItem(row[1], row[0])
    
    def refresh_schedule_table(self):
        cursor = self.db.get_connection().cursor()
        filter_type = self.schedule_filter_combo.currentText()
        
        query = """
            SELECT ts.Day, ts.StartTime, ts.EndTime, c.CourseCode, c.CourseName,
                   COALESCE(i.InstructorName, t.TAName, 'N/A') as Teacher,
                   r.RoomNumber, b.BuildingName, l.LevelName,
                   GROUP_CONCAT(DISTINCT sec.SectionNumber) as Sections,
                   CASE 
                       WHEN s.SessionType != 'Lecture' THEN GROUP_CONCAT(g.GroupNumber)
                       ELSE 'All'
                   END as Groups,
                   CASE 
                       WHEN s.SessionType = 'Lecture' THEN 'Lecture'
                       WHEN s.SessionType = 'Lab' THEN 'Lab'
                       WHEN s.SessionType = 'Tutorial' AND c.IsHalfSlot = 1 THEN 'Tutorial (Half)'
                       WHEN s.SessionType = 'Tutorial' THEN 'Tutorial'
                   END as SessionType
            FROM Schedule s
            JOIN Courses c ON s.CourseID = c.CourseID
            JOIN Groups g ON s.GroupID = g.GroupID
            JOIN Sections sec ON g.SectionID = sec.SectionID 
            JOIN Levels l ON g.LevelID = l.LevelID
            LEFT JOIN Instructors i ON s.InstructorID = i.InstructorID
            LEFT JOIN TAs t ON s.TAID = t.TAID
            JOIN Rooms r ON s.RoomID = r.RoomID
            JOIN Buildings b ON r.BuildingID = b.BuildingID
            JOIN TimeSlots ts ON s.TimeSlotID = ts.TimeSlotID
        """
        
        params = []
        if filter_type == "Day":
            query += " WHERE ts.Day = ?"
            params.append(self.schedule_value_combo.currentText())
        elif filter_type == "Instructor":
            query += " WHERE s.InstructorID = ?"
            params.append(self.schedule_value_combo.currentData())
        elif filter_type == "TA":
            query += " WHERE s.TAID = ?"
            params.append(self.schedule_value_combo.currentData())
        elif filter_type == "Course":
            query += " WHERE s.CourseID = ?"
            params.append(self.schedule_value_combo.currentData())
        elif filter_type == "Group":
            query += " WHERE s.GroupID = ?"
            params.append(self.schedule_value_combo.currentData())
        elif filter_type == "Room":
            query += " WHERE s.RoomID = ?"
            params.append(self.schedule_value_combo.currentData())
        
        query += """
            GROUP BY 
                CASE 
                    WHEN s.SessionType = 'Lecture' THEN ts.Day || ts.StartTime || c.CourseID || s.InstructorID || r.RoomID
                    ELSE s.ScheduleID 
                END
            ORDER BY ts.Day, ts.StartTime"""
        
        cursor.execute(query, params)
        schedule = cursor.fetchall()
        
        self.schedule_table.setRowCount(len(schedule))
        for i, row in enumerate(schedule):
            for j, value in enumerate(row):
                self.schedule_table.setItem(i, j, QTableWidgetItem(str(value)))
    
    def generate_schedule(self):
        # First, verify that we have all necessary data
        cursor = self.db.get_connection().cursor()
        
        # Check for buildings and rooms
        cursor.execute("SELECT RoomID, RoomType, RoomNumber FROM Rooms WHERE RoomType IN ('Hall', 'Theater', 'Classroom')")
        lecture_rooms = cursor.fetchall()
        if not lecture_rooms:
            QMessageBox.warning(self, "Error", "No halls, theaters, or classrooms available for lectures. Please add some rooms first.")
            return
            
            # Check if any course has a lab component
            cursor.execute("SELECT COUNT(*) FROM Courses WHERE HasLab = 1")
            if cursor.fetchone()[0] > 0:
                cursor.execute("SELECT COUNT(*) FROM Rooms WHERE RoomType = 'Lab'")
                if cursor.fetchone()[0] == 0:
                    QMessageBox.warning(self, "Error", "There are courses with labs but no lab rooms available. Please add some lab rooms first.")
                    return        # Check for courses
        cursor.execute("SELECT COUNT(*) FROM Courses")
        if cursor.fetchone()[0] == 0:
            QMessageBox.warning(self, "Error", "No courses to schedule. Please add some courses first.")
            return
            
        # Check for instructors and TAs
        cursor.execute("SELECT COUNT(*) FROM Instructors")
        if cursor.fetchone()[0] == 0:
            QMessageBox.warning(self, "Error", "No instructors available. Please add some instructors first.")
            return
            
        # Check for TAs only if there are courses with labs or tutorials
        cursor.execute("SELECT COUNT(*) FROM Courses WHERE HasLab = 1 OR HasTutorial = 1")
        if cursor.fetchone()[0] > 0:
            cursor.execute("SELECT COUNT(*) FROM TAs")
            if cursor.fetchone()[0] == 0:
                QMessageBox.warning(self, "Error", "There are courses with labs/tutorials but no TAs available. Please add some TAs first.")
                return
            
        # Check course assignments
        cursor.execute("SELECT COUNT(*) FROM Instructor_QualifiedCourses")
        if cursor.fetchone()[0] == 0:
            QMessageBox.warning(self, "Error", "No courses are assigned to instructors. Please assign instructors to courses.")
            return
            
        cursor.execute("SELECT COUNT(*) FROM TA_QualifiedCourses")
        if cursor.fetchone()[0] == 0:
            QMessageBox.warning(self, "Error", "No courses are assigned to TAs. Please assign TAs to courses.")
            return

        reply = QMessageBox.question(self, 'Generate Schedule', 
                                     'This will clear existing schedule and generate a new one. Continue?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            success, message = self.scheduler.generate_schedule()
            if success:
                cursor.execute("SELECT COUNT(*) FROM Schedule")
                count = cursor.fetchone()[0]
                QMessageBox.information(self, "Success", f"{message}\nGenerated {count} schedule entries.")
                self.refresh_schedule_table()
            else:
                QMessageBox.warning(self, "Error", f"Failed to generate schedule: {message}")
    
    def export_to_excel(self):
        cursor = self.db.get_connection().cursor()
        cursor.execute("""
            SELECT ts.Day, ts.StartTime, ts.EndTime, c.CourseCode, c.CourseName,
                   COALESCE(i.InstructorName, t.TAName, 'N/A') as Teacher,
                   r.RoomNumber, b.BuildingName, l.LevelName, g.GroupNumber, 
                   ts.Duration, s.SessionType
            FROM Schedule s
            JOIN Courses c ON s.CourseID = c.CourseID
            JOIN Groups g ON s.GroupID = g.GroupID
            JOIN Levels l ON g.LevelID = l.LevelID
            LEFT JOIN Instructors i ON s.InstructorID = i.InstructorID
            LEFT JOIN TAs t ON s.TAID = t.TAID
            JOIN Rooms r ON s.RoomID = r.RoomID
            JOIN Buildings b ON r.BuildingID = b.BuildingID
            JOIN TimeSlots ts ON s.TimeSlotID = ts.TimeSlotID
            ORDER BY ts.Day, ts.StartTime
        """)
        
        data = cursor.fetchall()
        
        if not data:
            QMessageBox.warning(self, "Error", "No schedule data to export")
            return
        
        filename, _ = QFileDialog.getSaveFileName(self, "Save Schedule", "", "Excel Files (*.xlsx)")
        
        if filename:
            df = pd.DataFrame(data, columns=[
                "Day", "StartTime", "EndTime", "CourseCode", "CourseName", 
                "Instructor/TA", "Room", "Building", "Level", "GroupNumber", "Duration", "SessionType"
            ])
            df.to_excel(filename, index=False)
            QMessageBox.information(self, "Success", f"Schedule exported to {filename}")
    
    def import_from_excel(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Import Excel", "", "Excel Files (*.xlsx *.xls)")
        
        if filename:
            try:
                # Try to read courses sheet
                df_courses = pd.read_excel(filename, sheet_name='Courses')
                
                cursor = self.db.get_connection().cursor()
                
                for _, row in df_courses.iterrows():
                    try:
                        # Get level ID
                        cursor.execute("SELECT LevelID FROM Levels WHERE LevelName = ?", (row['Level'],))
                        level_result = cursor.fetchone()
                        if not level_result:
                            continue
                        level_id = level_result[0]
                        
                        cursor.execute("""
                            INSERT INTO Courses (CourseCode, CourseName, LevelID, HasLab, HasTutorial, IsHalfSlot)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (row['CourseCode'], row['CourseName'], level_id, 
                             row.get('HasLab', 0), row.get('HasTutorial', 0), row.get('IsHalfSlot', 0)))
                    except:
                        continue
                
                self.db.get_connection().commit()
                self.refresh_courses_table()
                
                # Try to read instructors sheet
                try:
                    df_instructors = pd.read_excel(filename, sheet_name='Instructors')
                    for _, row in df_instructors.iterrows():
                        try:
                            cursor.execute("INSERT INTO Instructors (InstructorName) VALUES (?)", 
                                         (row['InstructorName'],))
                        except:
                            continue
                    self.db.get_connection().commit()
                    self.refresh_instructors_table()
                except:
                    pass
                
                # Try to read TAs sheet
                try:
                    df_tas = pd.read_excel(filename, sheet_name='TAs')
                    for _, row in df_tas.iterrows():
                        try:
                            cursor.execute("INSERT INTO TAs (TAName) VALUES (?)", (row['TAName'],))
                        except:
                            continue
                    self.db.get_connection().commit()
                    self.refresh_tas_table()
                except:
                    pass
                
                QMessageBox.information(self, "Success", "Data imported successfully")
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to import: {str(e)}")
    
    def clear_database(self):
        reply = QMessageBox.question(self, 'Clear Database', 
                                     'This will delete ALL data from the database. Are you sure?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.db.clear_database()
            self.refresh_all_tables()
            QMessageBox.information(self, "Success", "Database cleared successfully")
    
    def refresh_all_tables(self):
        self.refresh_buildings_table()
        self.refresh_rooms_table()
        self.refresh_levels_table()
        self.refresh_courses_table()
        self.refresh_instructors_table()
        self.refresh_tas_table()
        self.refresh_schedule_table()
        self.refresh_room_combo()
        self.refresh_course_combo()


def main():
    app = QApplication(sys.argv)
    window = TimetableApp()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()