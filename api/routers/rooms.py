from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from api import schemas, crud, auth
from api.database import get_db

router = APIRouter(prefix="/api/rooms", tags=["Rooms"])


@router.get("/", response_model=List[schemas.RoomResponse])
def list_rooms(
    building_id: Optional[int] = Query(None, description="Filter by building ID"),
    db: Session = Depends(get_db)
):
    """Get all rooms, optionally filtered by building"""
    return crud.get_rooms(db, building_id)


@router.post("/", response_model=schemas.RoomResponse, status_code=201)
def create_room(
    room: schemas.RoomCreate,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """Create a new room (requires authentication)"""
    return crud.create_room(db, room)


@router.get("/{room_id}", response_model=schemas.RoomResponse)
def get_room(room_id: int, db: Session = Depends(get_db)):
    """Get a specific room by ID"""
    room = crud.get_room(db, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.put("/{room_id}", response_model=schemas.RoomResponse)
def update_room(
    room_id: int,
    room: schemas.RoomCreate,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """Update a room (requires authentication)"""
    updated_room = crud.update_room(db, room_id, room)
    if not updated_room:
        raise HTTPException(status_code=404, detail="Room not found")
    return updated_room


@router.delete("/{room_id}", status_code=204)
def delete_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    """Delete a room (requires authentication)"""
    if not crud.delete_room(db, room_id):
        raise HTTPException(status_code=404, detail="Room not found")
