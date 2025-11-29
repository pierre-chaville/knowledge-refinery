import streamlit as st
from typing import Optional
from utils.file_manager import ensure_data_folders
from db.database import get_session
from services.lesson_service import LessonService
from services.course_service import CourseService
import streamlit.components.v1 as components
import base64
from pathlib import Path

# Configure page (must be first Streamlit command)
st.set_page_config(
    page_title="Knowledge Refinery",
    page_icon="🔬",
    layout="wide",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "Knowledge Refinery - Transform audio lessons into refined knowledge",
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

def create_audio_player(audio_path: Path, player_id: str = "audioPlayer") -> str:
    """
    Create a custom HTML5 audio player with seek functionality.
    Returns HTML code with embedded audio as base64.
    """
    # Read audio file and encode as base64
    with open(audio_path, "rb") as audio_file:
        audio_bytes = audio_file.read()
        audio_base64 = base64.b64encode(audio_bytes).decode()
    
    # Determine MIME type based on file extension
    ext = audio_path.suffix.lower()
    mime_type = "audio/mpeg" if ext == ".mp3" else f"audio/{ext[1:]}"
    
    html_code = f"""
    <div style="margin: 20px 0;">
        <audio id="{player_id}" controls style="width: 100%;">
            <source src="data:{mime_type};base64,{audio_base64}" type="{mime_type}">
            Your browser does not support the audio element.
        </audio>
    </div>
    <script>
        // Function to seek to a specific time
        function seekTo(seconds) {{
            var audio = document.getElementById('{player_id}');
            if (audio) {{
                audio.currentTime = seconds;
                audio.play();
            }}
        }}
        
        // Listen for messages from Streamlit
        window.addEventListener('message', function(event) {{
            if (event.data && event.data.type === 'seek') {{
                seekTo(event.data.time);
            }}
        }});
    </script>
    """
    return html_code

st.title("🔬 Knowledge Refinery")
st.caption("Transform audio lessons into refined knowledge")

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

if not processed_lessons:
    st.info("📝 No processed lessons found. Go to **Process** to transcribe and analyze your lessons.")
else:
    # Get selected lesson
    lesson = lesson_service.get_lesson(selected_lesson_id)
    
    if lesson:
        # Display lesson title and date below main heading
        st.markdown(f"### 📖 {lesson.title}")
        st.caption(f"📅 {lesson.date.strftime('%A, %B %d, %Y')}")
        
        st.markdown("---")
        
        # Tabs for Lesson Details, Summary, Corrected Transcript, Initial Transcript
        tab2, tab3, tab4, tab1 = st.tabs(["📄 Summary", "✅ Corrected Transcript", "📝 Initial Transcript", "📋 Lesson"])
        
        # ========== LESSON TAB ==========
        with tab1:
            st.subheader("Lesson Details")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**ID:** {lesson.id}")
                st.write(f"**Title:** {lesson.title}")
                st.write(f"**Date:** {lesson.date.strftime('%Y-%m-%d')}")
                st.write(f"**Duration:** {format_duration(lesson.duration)}")
            
            with col2:
                course = course_service.get_course(lesson.course_id) if lesson.course_id else None
                st.write(f"**Course:** {course.name if course else 'N/A'}")
                st.write(f"**Filename:** {lesson.filename}")
                
                # Show themes
                from services.theme_service import ThemeService
                theme_service = ThemeService(session)
                theme_ids = lesson.get_themes()
                if theme_ids:
                    theme_objs = theme_service.get_themes_by_ids(theme_ids)
                    theme_names = [t.name for t in theme_objs]
                    st.write(f"**Themes:** {', '.join(theme_names)}")
                else:
                    st.write(f"**Themes:** None")
            
            # Show status
            st.markdown("---")
            st.subheader("Processing Status")
            col_status1, col_status2, col_status3 = st.columns(3)
            
            with col_status1:
                if lesson.transcript:
                    st.success("✅ Transcript Available")
                    metadata = lesson.get_transcript_metadata()
                    if metadata:
                        st.caption(f"Model: {metadata.model_size or 'N/A'}")
                        st.caption(f"Device: {metadata.device or 'N/A'}")
                else:
                    st.warning("⏳ No Transcript")
            
            with col_status2:
                if lesson.corrected_transcript:
                    st.success("✅ Corrected Transcript")
                    metadata = lesson.get_correction_metadata()
                    if metadata:
                        st.caption(f"Provider: {metadata.provider or 'N/A'}")
                        st.caption(f"Model: {metadata.model or 'N/A'}")
                else:
                    st.warning("⏳ No Correction")
            
            with col_status3:
                if lesson.summary:
                    st.success("✅ Summary Available")
                    metadata = lesson.get_summary_metadata()
                    if metadata:
                        st.caption(f"Provider: {metadata.provider or 'N/A'}")
                        st.caption(f"Model: {metadata.model or 'N/A'}")
                else:
                    st.warning("⏳ No Summary")
            
            # Check audio file
            from utils.file_manager import get_audio_file_path
            audio_path = get_audio_file_path(lesson.id, lesson.filename)
            st.markdown("---")
            if audio_path.exists():
                file_size = audio_path.stat().st_size / 1024 / 1024
                st.info(f"🎵 Audio file: {lesson.filename} ({file_size:.2f} MB)")
            else:
                st.error(f"❌ Audio file not found: {lesson.filename}")
        
        # ========== SUMMARY TAB ==========
        with tab2:
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
                
                st.markdown("**Summary:**")
                st.markdown(lesson.summary)
                
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
        with tab3:
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
                
                # Check if audio file exists (for potential audio playback)
                from utils.file_manager import get_audio_file_path
                audio_path = get_audio_file_path(lesson.id, lesson.filename)
                
                # Try to get original transcript segments for timestamps
                original_segments = lesson_service.get_transcript_segments(lesson)
                
                if original_segments and audio_path.exists():
                    # Initialize session state for seek time
                    if f'seek_time_corrected_{lesson.id}' not in st.session_state:
                        st.session_state[f'seek_time_corrected_{lesson.id}'] = None
                    
                    # Display custom audio player
                    st.subheader("🎵 Audio Player")
                    player_id = f"audioPlayer_corrected_{lesson.id}"
                    
                    # Create the audio player HTML
                    audio_html = create_audio_player(audio_path, player_id)
                    
                    # If a seek time is set, add JavaScript to seek
                    seek_time = st.session_state[f'seek_time_corrected_{lesson.id}']
                    if seek_time is not None:
                        audio_html += f"""
                        <script>
                            setTimeout(function() {{
                                seekTo({seek_time});
                            }}, 100);
                        </script>
                        """
                        # Reset seek time after using it
                        st.session_state[f'seek_time_corrected_{lesson.id}'] = None
                    
                    components.html(audio_html, height=80)
                    
                    st.markdown("---")
                    st.subheader("📝 Interactive Corrected Transcript")
                    st.caption("🔊 Click on timestamps to jump to that position in the audio player above (timestamps from original transcript)")
                    
                    # Get corrected text and try to align with original segments
                    corrected_text = lesson_service.get_corrected_transcript_text(lesson)
                    corrected_lines = corrected_text.split('\n') if corrected_text else []
                    
                    # Display with timestamps from original segments
                    for i, seg in enumerate(original_segments):
                        start_time = seg['start']
                        end_time = seg['end']
                        
                        # Use corrected text if available, otherwise use original
                        if i < len(corrected_lines):
                            text = corrected_lines[i]
                        else:
                            text = seg['text']
                        
                        # Format timestamps
                        start_str = format_timestamp(start_time)
                        end_str = format_timestamp(end_time)
                        
                        # Create columns for timestamp button and text
                        col1, col2 = st.columns([1, 5])
                        
                        with col1:
                            # Clickable timestamp button
                            if st.button(
                                f"🔊 {start_str}",
                                key=f"timestamp_corrected_home_{lesson.id}_{i}",
                                help=f"Click to jump to {start_str}"
                            ):
                                # Set the seek time and rerun
                                st.session_state[f'seek_time_corrected_{lesson.id}'] = start_time
                                st.rerun()
                        
                        with col2:
                            st.markdown(f"**[{start_str} - {end_str}]** {text}")
                    
                    st.markdown("---")
                    
                    # Download button
                    st.download_button(
                        label="📥 Download Corrected Transcript",
                        data=corrected_text or "",
                        file_name=f"{lesson.title}_corrected.txt",
                        mime="text/plain",
                        key="download_corrected_home"
                    )
                else:
                    # No segments or audio, display as plain text
                    corrected_text = lesson_service.get_corrected_transcript_text(lesson)
                    st.text_area(
                        "Corrected Transcript",
                        corrected_text or "",
                        height=400,
                        key=f"home_corrected_display_{lesson.id}"
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
        with tab4:
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
                
                # Check if audio file exists
                from utils.file_manager import get_audio_file_path
                audio_path = get_audio_file_path(lesson.id, lesson.filename)
                
                # Check if it's segments or plain text
                transcript_segments = lesson_service.get_transcript_segments(lesson)
                
                if transcript_segments and audio_path.exists():
                    # Initialize session state for seek time
                    if f'seek_time_transcript_{lesson.id}' not in st.session_state:
                        st.session_state[f'seek_time_transcript_{lesson.id}'] = None
                    
                    # Display custom audio player
                    st.subheader("🎵 Audio Player")
                    player_id = f"audioPlayer_transcript_{lesson.id}"
                    
                    # Create the audio player HTML
                    audio_html = create_audio_player(audio_path, player_id)
                    
                    # If a seek time is set, add JavaScript to seek
                    seek_time = st.session_state[f'seek_time_transcript_{lesson.id}']
                    if seek_time is not None:
                        audio_html += f"""
                        <script>
                            setTimeout(function() {{
                                seekTo({seek_time});
                            }}, 100);
                        </script>
                        """
                        # Reset seek time after using it
                        st.session_state[f'seek_time_transcript_{lesson.id}'] = None
                    
                    components.html(audio_html, height=80)
                    
                    st.markdown("---")
                    st.subheader("📝 Interactive Transcript")
                    st.caption("🔊 Click on timestamps to jump to that position in the audio player above")
                    
                    # Display transcript with clickable timestamps
                    for i, seg in enumerate(transcript_segments):
                        start_time = seg['start']
                        end_time = seg['end']
                        text = seg['text']
                        
                        # Format timestamps
                        start_str = format_timestamp(start_time)
                        end_str = format_timestamp(end_time)
                        
                        # Create columns for timestamp button and text
                        col1, col2 = st.columns([1, 5])
                        
                        with col1:
                            # Clickable timestamp button
                            if st.button(
                                f"🔊 {start_str}",
                                key=f"timestamp_home_{lesson.id}_{i}",
                                help=f"Click to jump to {start_str}"
                            ):
                                # Set the seek time and rerun
                                st.session_state[f'seek_time_transcript_{lesson.id}'] = start_time
                                st.rerun()
                        
                        with col2:
                            st.markdown(f"**[{start_str} - {end_str}]** {text}")
                    
                    st.markdown("---")
                    
                    # Also provide full text version for download
                    transcript_text = format_transcript_with_timestamps(transcript_segments)
                    
                    # Download button
                    st.download_button(
                        label="📥 Download Transcript",
                        data=transcript_text or "",
                        file_name=f"{lesson.title}_transcript.txt",
                        mime="text/plain",
                        key="download_transcript_home"
                    )
                    
                elif transcript_segments:
                    # Has segments but no audio file
                    st.warning("⚠️ Audio file not found. Displaying transcript without audio player.")
                    transcript_text = format_transcript_with_timestamps(transcript_segments)
                    st.text_area(
                        "Initial Transcript",
                        transcript_text or "",
                        height=400,
                        key=f"home_transcript_display_{lesson.id}"
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
                    # Plain text transcript
                    transcript_text = lesson_service.get_transcript_text(lesson)
                    st.text_area(
                        "Initial Transcript",
                        transcript_text or "",
                        height=400,
                        key=f"home_transcript_display_{lesson.id}"
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

