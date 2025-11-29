"""Business logic for courses"""
from typing import List, Optional
from sqlmodel import Session
from db import crud
from db.models import Course

class CourseService:
    """Service for course operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_course(self, name: str, description: Optional[str] = None) -> Course:
        """Create a new course"""
        return crud.create_course(self.session, name, description)
    
    def get_course(self, course_id: int) -> Optional[Course]:
        """Get course by ID"""
        return crud.get_course(self.session, course_id)
    
    def get_all_courses(self) -> List[Course]:
        """Get all courses"""
        return crud.get_all_courses(self.session)
    
    def update_course(self, course_id: int, name: Optional[str] = None, description: Optional[str] = None) -> Optional[Course]:
        """Update a course"""
        return crud.update_course(self.session, course_id, name, description)
    
    def delete_course(self, course_id: int) -> bool:
        """Delete a course"""
        return crud.delete_course(self.session, course_id)

