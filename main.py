from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from api import models, auth, schemas, crud
from api.database import engine, SessionLocal
from api.routers import (
    auth as auth_router,
    buildings,
    halls,
    rooms,
    levels,
    sections,
    groups,
    courses,
    instructors,
    tas,
    schedule
)


def init_database():
    """Initialize database tables and seed data"""
    # Create all tables
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Seed time slots if empty
        timeslot_count = db.query(models.TimeSlot).count()
        if timeslot_count == 0:
            print("Seeding time slots...")
            time_slots = []
            
            # Days: Sunday through Thursday
            days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']
            
            for day in days:
                # 90-minute slots (09:00 - 15:45)
                time_slots.extend([
                    models.TimeSlot(day=day, start_time='09:00', end_time='10:30', duration=90),
                    models.TimeSlot(day=day, start_time='10:45', end_time='12:15', duration=90),
                    models.TimeSlot(day=day, start_time='12:30', end_time='14:00', duration=90),
                    models.TimeSlot(day=day, start_time='14:15', end_time='15:45', duration=90),
                ])
                
                # 45-minute slots (09:00 - 15:45)
                time_slots.extend([
                    models.TimeSlot(day=day, start_time='09:00', end_time='09:45', duration=45),
                    models.TimeSlot(day=day, start_time='09:45', end_time='10:30', duration=45),
                    models.TimeSlot(day=day, start_time='10:45', end_time='11:30', duration=45),
                    models.TimeSlot(day=day, start_time='11:30', end_time='12:15', duration=45),
                    models.TimeSlot(day=day, start_time='12:30', end_time='13:15', duration=45),
                    models.TimeSlot(day=day, start_time='13:15', end_time='14:00', duration=45),
                    models.TimeSlot(day=day, start_time='14:15', end_time='15:00', duration=45),
                    models.TimeSlot(day=day, start_time='15:00', end_time='15:45', duration=45),
                ])
            
            db.add_all(time_slots)
            db.commit()
            print(f"Seeded {len(time_slots)} time slots")
        
        # Create default admin user if it doesn't exist
        admin_user = crud.get_user_by_username(db, "admin")
        if not admin_user:
            print("Creating default admin user...")
            hashed_password = auth.get_password_hash("admin123")
            user_create = schemas.UserCreate(
                username="admin",
                password="admin123",
                is_admin=True
            )
            crud.create_user(db, user_create, hashed_password)
            print("Default admin user created (username: admin, password: admin123)")
            print("IMPORTANT: Please change the admin password immediately!")
    
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    print("Starting University Timetable Scheduling System...")
    init_database()
    print("Database initialized successfully")
    print("Server ready. Access Swagger UI at http://localhost:8000/docs")
    
    yield
    
    # Shutdown
    print("Shutting down...")


# Create FastAPI application
app = FastAPI(
    title="University Timetable Scheduling System",
    description="FastAPI-based timetable scheduling system with CSP algorithm",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (they already have /api prefix)
app.include_router(auth_router.router)
app.include_router(buildings.router)
app.include_router(halls.router)
app.include_router(rooms.router)
app.include_router(levels.router)
app.include_router(sections.router)
app.include_router(groups.router)
app.include_router(courses.router)
app.include_router(instructors.router)
app.include_router(tas.router)
app.include_router(schedule.router)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def root():
    """Serve the main index.html page"""
    return FileResponse("static/index.html")


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)