"""Business logic for lessons"""
from typing import List, Optional
from datetime import datetime
from sqlmodel import Session
from db import crud
from db.models import Lesson
import json

class LessonService:
    """Service for lesson operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_lesson(
        self,
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
        return crud.create_lesson(
            self.session,
            title=title,
            filename=filename,
            course_id=course_id,
            date=date,
            duration=duration,
            transcript=transcript,
            corrected_transcript=corrected_transcript,
            summary=summary,
            theme_ids=theme_ids
        )
    
    def get_lesson(self, lesson_id: int) -> Optional[Lesson]:
        """Get lesson by ID"""
        return crud.get_lesson(self.session, lesson_id)
    
    def get_all_lessons(self, course_id: Optional[int] = None) -> List[Lesson]:
        """Get all lessons, optionally filtered by course"""
        return crud.get_all_lessons(self.session, course_id)
    
    def get_lessons_by_course(self, course_id: int) -> List[Lesson]:
        """Get all lessons for a specific course"""
        return crud.get_all_lessons(self.session, course_id=course_id)
    
    def update_lesson(
        self,
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
        return crud.update_lesson(
            self.session,
            lesson_id,
            title=title,
            filename=filename,
            course_id=course_id,
            date=date,
            duration=duration,
            transcript=transcript,
            corrected_transcript=corrected_transcript,
            summary=summary,
            theme_ids=theme_ids,
            transcript_metadata=transcript_metadata,
            correction_metadata=correction_metadata,
            summary_metadata=summary_metadata
        )
    
    def delete_lesson(self, lesson_id: int) -> bool:
        """Delete a lesson"""
        return crud.delete_lesson(self.session, lesson_id)
    
    def duplicate_lesson(self, lesson_id: int, new_title_suffix: str = " (Copy)") -> Optional[Lesson]:
        """
        Duplicate a lesson with all its data and audio file.
        Creates a copy with a new ID and copies the audio file.
        
        Args:
            lesson_id: ID of the lesson to duplicate
            new_title_suffix: Suffix to add to the new lesson title
            
        Returns:
            The newly created lesson or None if original lesson not found
        """
        from pathlib import Path
        import shutil
        from utils.file_manager import get_audio_file_path
        
        # Get the original lesson
        original_lesson = self.get_lesson(lesson_id)
        if not original_lesson:
            return None
        
        # Create new lesson with copied data
        new_lesson = self.create_lesson(
            title=original_lesson.title + new_title_suffix,
            filename=original_lesson.filename,
            course_id=original_lesson.course_id,
            date=original_lesson.date,
            duration=original_lesson.duration,
            transcript=original_lesson.transcript,
            corrected_transcript=original_lesson.corrected_transcript,
            summary=original_lesson.summary,
            theme_ids=original_lesson.get_themes()
        )
        
        # Copy metadata if present
        if original_lesson.transcript_metadata or original_lesson.correction_metadata or original_lesson.summary_metadata:
            self.update_lesson(
                new_lesson.id,
                transcript_metadata=original_lesson.transcript_metadata,
                correction_metadata=original_lesson.correction_metadata,
                summary_metadata=original_lesson.summary_metadata
            )
        
        # Copy the audio file with new ID
        original_audio_path = get_audio_file_path(original_lesson.id, original_lesson.filename)
        if original_audio_path.exists():
            new_audio_path = get_audio_file_path(new_lesson.id, new_lesson.filename)
            shutil.copy2(original_audio_path, new_audio_path)
        
        # Refresh to get updated lesson
        return self.get_lesson(new_lesson.id)
    
    def save_transcript(
        self, 
        lesson_id: int, 
        transcript_data,
        model_size: Optional[str] = None,
        device: Optional[str] = None,
        compute_type: Optional[str] = None,
        beam_size: Optional[int] = None,
        vad_filter: Optional[bool] = None,
        language: Optional[str] = None,
        initial_prompt: Optional[str] = None
    ) -> Optional[Lesson]:
        """
        Save transcript as JSON dict with metadata.
        
        Args:
            transcript_data: Either a string (text) or list of segments (dicts with start, end, text)
        """
        from db.models import TranscriptMetadata
        
        if isinstance(transcript_data, list):
            # List of segments
            transcript_dict = {"segments": transcript_data}
        else:
            # Plain text
            transcript_dict = {"text": transcript_data}
        
        metadata = TranscriptMetadata(
            model_size=model_size,
            device=device,
            compute_type=compute_type,
            beam_size=beam_size,
            vad_filter=vad_filter,
            language=language,
            initial_prompt=initial_prompt
        )
        
        return self.update_lesson(
            lesson_id, 
            transcript=transcript_dict,
            transcript_metadata=metadata.model_dump()
        )
    
    def save_corrected_transcript(
        self, 
        lesson_id: int, 
        corrected_text: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        prompt: Optional[str] = None
    ) -> Optional[Lesson]:
        """Save corrected transcript as JSON dict with metadata"""
        from db.models import Metadata
        corrected_dict = {"text": corrected_text}
        metadata = Metadata(
            provider=provider,
            model=model,
            temperature=temperature,
            prompt=prompt
        )
        return self.update_lesson(
            lesson_id, 
            corrected_transcript=corrected_dict,
            correction_metadata=metadata.model_dump()
        )
    
    def save_summary(
        self, 
        lesson_id: int, 
        summary_text: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        prompt: Optional[str] = None
    ) -> Optional[Lesson]:
        """Save summary with metadata"""
        from db.models import Metadata
        metadata = Metadata(
            provider=provider,
            model=model,
            temperature=temperature,
            prompt=prompt
        )
        return self.update_lesson(
            lesson_id, 
            summary=summary_text,
            summary_metadata=metadata.model_dump()
        )
    
    def get_transcript_text(self, lesson: Lesson) -> Optional[str]:
        """Extract transcript text from JSON dict"""
        if lesson.transcript:
            # If it's already a dict (JSON column)
            if isinstance(lesson.transcript, dict):
                # Check if we have segments (new format)
                if "segments" in lesson.transcript:
                    segments = lesson.transcript["segments"]
                    return "\n".join([seg["text"].strip() for seg in segments])
                # Otherwise get text field (old format)
                return lesson.transcript.get("text")
            # Fallback for old string format
            elif isinstance(lesson.transcript, str):
                try:
                    data = json.loads(lesson.transcript)
                    if "segments" in data:
                        segments = data["segments"]
                        return "\n".join([seg["text"].strip() for seg in segments])
                    return data.get("text", lesson.transcript)
                except json.JSONDecodeError:
                    return lesson.transcript
        return None
    
    def get_transcript_segments(self, lesson: Lesson) -> Optional[list]:
        """Extract transcript segments from JSON dict"""
        if lesson.transcript:
            # If it's already a dict (JSON column)
            if isinstance(lesson.transcript, dict):
                return lesson.transcript.get("segments")
            # Fallback for old string format
            elif isinstance(lesson.transcript, str):
                try:
                    data = json.loads(lesson.transcript)
                    return data.get("segments")
                except json.JSONDecodeError:
                    return None
        return None
    
    def get_corrected_transcript_text(self, lesson: Lesson) -> Optional[str]:
        """Extract corrected transcript text from JSON dict"""
        if lesson.corrected_transcript:
            # If it's already a dict (JSON column), get the text
            if isinstance(lesson.corrected_transcript, dict):
                return lesson.corrected_transcript.get("text")
            # Fallback for old string format
            elif isinstance(lesson.corrected_transcript, str):
                try:
                    data = json.loads(lesson.corrected_transcript)
                    return data.get("text", lesson.corrected_transcript)
                except json.JSONDecodeError:
                    return lesson.corrected_transcript
        return None

