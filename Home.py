import streamlit as st
from typing import Optional
from utils.file_manager import ensure_data_folders
from db.database import get_session
from services.lesson_service import LessonService
from services.course_service import CourseService

# Configure page (must be first Streamlit command)
st.set_page_config(
    page_title="Processed Lessons",
    page_icon="📚",
    layout="wide",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": None,
    },
)

# Initialize database and folders once
if "app_initialized" not in st.session_state:
    ensure_data_folders()
    from db.database import init_db
    init_db()
    st.session_state["app_initialized"] = True

def format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def format_transcript_with_timestamps(segments: list) -> str:
    """Format transcript segments with timestamps"""
    lines = []
    for seg in segments:
        start_time = format_timestamp(seg['start'])
        end_time = format_timestamp(seg['end'])
        lines.append(f"[{start_time} - {end_time}] {seg['text']}")
    return "\n".join(lines)

def format_duration(seconds: Optional[float]) -> str:
    """Format duration in seconds to readable format"""
    if seconds is None:
        return "N/A"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if minutes >= 60:
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}h {mins}m {secs}s"
    return f"{minutes}m {secs}s"

st.title("📚 Processed Lessons")

# Get database session
session = next(get_session())
lesson_service = LessonService(session)
course_service = CourseService(session)

# ========== SIDEBAR SELECTORS ==========
with st.sidebar:
    st.header("Filters")
    
    # Course selector
    courses = course_service.get_all_courses()
    course_options = {"All Courses": None}
    for course in courses:
        course_options[course.name] = course.id

    selected_course_name = st.selectbox(
        "Select Course",
        options=list(course_options.keys()),
        key="home_course_selector"
    )
    selected_course_id = course_options[selected_course_name]

    # Get lessons filtered by course
    if selected_course_id:
        lessons = lesson_service.get_lessons_by_course(selected_course_id)
    else:
        lessons = lesson_service.get_all_lessons()

    # Filter only processed lessons (with at least transcript or summary)
    processed_lessons = [l for l in lessons if l.transcript or l.corrected_transcript or l.summary]

    if processed_lessons:
        # Lesson selector
        lesson_options = {}
        for lesson in processed_lessons:
            status_parts = []
            if lesson.transcript:
                status_parts.append("📝")
            if lesson.corrected_transcript:
                status_parts.append("✅")
            if lesson.summary:
                status_parts.append("📄")
            status = " ".join(status_parts)
            lesson_options[f"{lesson.title} {status}"] = lesson.id
        
        selected_lesson_name = st.selectbox(
            "Select Lesson",
            options=list(lesson_options.keys()),
            key="home_lesson_selector"
        )
        selected_lesson_id = lesson_options[selected_lesson_name]

st.markdown("---")

if not processed_lessons:
    st.info("📝 No processed lessons found. Go to **Process** to transcribe and analyze your lessons.")
else:
    # Get selected lesson
    lesson = lesson_service.get_lesson(selected_lesson_id)
    
    if lesson:
        # Display lesson details
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Date", lesson.date.strftime("%Y-%m-%d"))
        with col2:
            st.metric("Duration", format_duration(lesson.duration))
        with col3:
            course = course_service.get_course(lesson.course_id) if lesson.course_id else None
            st.metric("Course", course.name if course else "N/A")
        with col4:
            st.metric("File", lesson.filename)
        
        st.markdown("---")
        
        # Tabs for Summary, Corrected Transcript, Initial Transcript
        tab1, tab2, tab3 = st.tabs(["📄 Summary", "✅ Corrected Transcript", "📝 Initial Transcript"])
        
        # ========== SUMMARY TAB ==========
        with tab1:
            if lesson.summary:
                # Display metadata
                metadata = lesson.get_summary_metadata()
                if metadata:
                    st.subheader("Summary Details")
                    col_meta1, col_meta2, col_meta3 = st.columns(3)
                    with col_meta1:
                        st.caption(f"**Provider:** {metadata.provider or 'N/A'}")
                    with col_meta2:
                        st.caption(f"**Model:** {metadata.model or 'N/A'}")
                    with col_meta3:
                        st.caption(f"**Temperature:** {metadata.temperature or 'N/A'}")
                    if metadata.prompt:
                        with st.expander("View Prompt Used"):
                            st.text(metadata.prompt)
                    st.markdown("---")
                
                st.text_area(
                    "Summary",
                    lesson.summary,
                    height=400,
                    key="home_summary_display"
                )
                
                # Download button
                st.download_button(
                    label="📥 Download Summary",
                    data=lesson.summary,
                    file_name=f"{lesson.title}_summary.txt",
                    mime="text/plain",
                    key="download_summary_home"
                )
            else:
                st.info("No summary available for this lesson. Go to **Process** → **Summarize** to create one.")
        
        # ========== CORRECTED TRANSCRIPT TAB ==========
        with tab2:
            if lesson.corrected_transcript:
                # Display metadata
                metadata = lesson.get_correction_metadata()
                if metadata:
                    st.subheader("Correction Details")
                    col_meta1, col_meta2, col_meta3 = st.columns(3)
                    with col_meta1:
                        st.caption(f"**Provider:** {metadata.provider or 'N/A'}")
                    with col_meta2:
                        st.caption(f"**Model:** {metadata.model or 'N/A'}")
                    with col_meta3:
                        st.caption(f"**Temperature:** {metadata.temperature or 'N/A'}")
                    if metadata.prompt:
                        with st.expander("View Prompt Used"):
                            st.text(metadata.prompt)
                    st.markdown("---")
                
                corrected_text = lesson_service.get_corrected_transcript_text(lesson)
                st.text_area(
                    "Corrected Transcript",
                    corrected_text or "",
                    height=400,
                    key="home_corrected_display"
                )
                
                # Download button
                st.download_button(
                    label="📥 Download Corrected Transcript",
                    data=corrected_text or "",
                    file_name=f"{lesson.title}_corrected.txt",
                    mime="text/plain",
                    key="download_corrected_home"
                )
            else:
                st.info("No corrected transcript available. Go to **Process** → **Correct** to create one.")
        
        # ========== INITIAL TRANSCRIPT TAB ==========
        with tab3:
            if lesson.transcript:
                # Display metadata
                metadata = lesson.get_transcript_metadata()
                if metadata:
                    st.subheader("Transcription Details")
                    col_meta1, col_meta2, col_meta3, col_meta4 = st.columns(4)
                    with col_meta1:
                        st.caption(f"**Model:** {metadata.model_size or 'N/A'}")
                        st.caption(f"**Device:** {metadata.device or 'N/A'}")
                    with col_meta2:
                        st.caption(f"**Compute Type:** {metadata.compute_type or 'N/A'}")
                        st.caption(f"**Beam Size:** {metadata.beam_size or 'N/A'}")
                    with col_meta3:
                        st.caption(f"**Language:** {metadata.language or 'auto'}")
                        st.caption(f"**VAD Filter:** {'Yes' if metadata.vad_filter else 'No'}")
                    with col_meta4:
                        if metadata.initial_prompt:
                            with st.expander("View Initial Prompt"):
                                st.text(metadata.initial_prompt)
                    st.markdown("---")
                
                # Check if it's segments or plain text
                transcript_segments = lesson_service.get_transcript_segments(lesson)
                if transcript_segments:
                    # Format with timestamps
                    transcript_text = format_transcript_with_timestamps(transcript_segments)
                else:
                    # Plain text
                    transcript_text = lesson_service.get_transcript_text(lesson)
                
                st.text_area(
                    "Initial Transcript",
                    transcript_text or "",
                    height=400,
                    key="home_transcript_display"
                )
                
                # Download button
                st.download_button(
                    label="📥 Download Transcript",
                    data=transcript_text or "",
                    file_name=f"{lesson.title}_transcript.txt",
                    mime="text/plain",
                    key="download_transcript_home"
                )
            else:
                st.info("No transcript available. Go to **Process** → **Transcribe** to create one.")

