"""CRUD operations for database models"""
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime
from db.models import Lesson, Course, Theme

# Course CRUD
def create_course(session: Session, name: str, description: Optional[str] = None) -> Course:
    """Create a new course"""
    course = Course(name=name, description=description)
    session.add(course)
    session.commit()
    session.refresh(course)
    return course

def get_course(session: Session, course_id: int) -> Optional[Course]:
    """Get course by ID"""
    return session.get(Course, course_id)

def get_all_courses(session: Session) -> List[Course]:
    """Get all courses"""
    statement = select(Course)
    return list(session.exec(statement).all())

def update_course(session: Session, course_id: int, name: Optional[str] = None, description: Optional[str] = None) -> Optional[Course]:
    """Update a course"""
    course = session.get(Course, course_id)
    if course:
        if name is not None:
            course.name = name
        if description is not None:
            course.description = description
        session.add(course)
        session.commit()
        session.refresh(course)
    return course

def delete_course(session: Session, course_id: int) -> bool:
    """Delete a course"""
    course = session.get(Course, course_id)
    if course:
        session.delete(course)
        session.commit()
        return True
    return False

# Theme CRUD
def create_theme(session: Session, name: str) -> Theme:
    """Create a new theme"""
    theme = Theme(name=name)
    session.add(theme)
    session.commit()
    session.refresh(theme)
    return theme

def get_theme(session: Session, theme_id: int) -> Optional[Theme]:
    """Get theme by ID"""
    return session.get(Theme, theme_id)

def get_all_themes(session: Session) -> List[Theme]:
    """Get all themes"""
    statement = select(Theme)
    return list(session.exec(statement).all())

def get_themes_by_ids(session: Session, theme_ids: List[int]) -> List[Theme]:
    """Get themes by list of IDs"""
    if not theme_ids:
        return []
    statement = select(Theme).where(Theme.id.in_(theme_ids))
    return list(session.exec(statement).all())

def update_theme(session: Session, theme_id: int, name: str) -> Optional[Theme]:
    """Update a theme"""
    theme = session.get(Theme, theme_id)
    if theme:
        theme.name = name
        session.add(theme)
        session.commit()
        session.refresh(theme)
    return theme

def delete_theme(session: Session, theme_id: int) -> bool:
    """Delete a theme"""
    theme = session.get(Theme, theme_id)
    if theme:
        session.delete(theme)
        session.commit()
        return True
    return False

# Lesson CRUD
def create_lesson(
    session: Session,
    title: str,
    filename: str,
    course_id: Optional[int] = None,
    date: Optional[datetime] = None,
    duration: Optional[float] = None,
    transcript: Optional[str] = None,
    corrected_transcript: Optional[str] = None,
    summary: Optional[str] = None,
    theme_ids: Optional[List[int]] = None
) -> Lesson:
    """Create a new lesson"""
    lesson = Lesson(
        title=title,
        filename=filename,
        course_id=course_id,
        date=date or datetime.now(),
        duration=duration,
        transcript=transcript,
        corrected_transcript=corrected_transcript,
        summary=summary
    )
    if theme_ids:
        lesson.set_themes(theme_ids)
    session.add(lesson)
    session.commit()
    session.refresh(lesson)
    return lesson

def get_lesson(session: Session, lesson_id: int) -> Optional[Lesson]:
    """Get lesson by ID"""
    return session.get(Lesson, lesson_id)

def get_all_lessons(session: Session, course_id: Optional[int] = None) -> List[Lesson]:
    """Get all lessons, optionally filtered by course"""
    if course_id:
        statement = select(Lesson).where(Lesson.course_id == course_id)
    else:
        statement = select(Lesson)
    return list(session.exec(statement).all())

def update_lesson(
    session: Session,
    lesson_id: int,
    title: Optional[str] = None,
    filename: Optional[str] = None,
    course_id: Optional[int] = None,
    date: Optional[datetime] = None,
    duration: Optional[float] = None,
    transcript: Optional[str] = None,
    corrected_transcript: Optional[str] = None,
    summary: Optional[str] = None,
    theme_ids: Optional[List[int]] = None,
    transcript_metadata: Optional[dict] = None,
    correction_metadata: Optional[dict] = None,
    summary_metadata: Optional[dict] = None
) -> Optional[Lesson]:
    """Update a lesson"""
    lesson = session.get(Lesson, lesson_id)
    if lesson:
        if title is not None:
            lesson.title = title
        if filename is not None:
            lesson.filename = filename
        if course_id is not None:
            lesson.course_id = course_id
        if date is not None:
            lesson.date = date
        if duration is not None:
            lesson.duration = duration
        if transcript is not None:
            lesson.transcript = transcript
        if corrected_transcript is not None:
            lesson.corrected_transcript = corrected_transcript
        if summary is not None:
            lesson.summary = summary
        if theme_ids is not None:
            lesson.set_themes(theme_ids)
        if transcript_metadata is not None:
            lesson.transcript_metadata = transcript_metadata
        if correction_metadata is not None:
            lesson.correction_metadata = correction_metadata
        if summary_metadata is not None:
            lesson.summary_metadata = summary_metadata
        
        session.add(lesson)
        session.commit()
        session.refresh(lesson)
    return lesson

def delete_lesson(session: Session, lesson_id: int) -> bool:
    """Delete a lesson"""
    lesson = session.get(Lesson, lesson_id)
    if lesson:
        session.delete(lesson)
        session.commit()
        return True
    return False

