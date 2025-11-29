import streamlit as st
from datetime import datetime
from pathlib import Path
from io import BytesIO
from mutagen.mp3 import MP3
from db.database import get_session
from services.lesson_service import LessonService
from services.course_service import CourseService
from services.theme_service import ThemeService
from utils.file_manager import ensure_data_folders, extract_title_from_filename, extract_date_from_filename, get_audio_file_path


def format_duration(seconds: float | None) -> str:
    """Format duration in seconds to mm:ss plus raw seconds."""
    if seconds is None:
        return "Not set"
    try:
        total = max(0.0, float(seconds))
    except (TypeError, ValueError):
        return "Not set"
    minutes = int(total // 60)
    secs = int(total % 60)
    return f"{minutes:02d}:{secs:02d} ({total:.1f} s)"

def app():
    st.title("📚 Lessons Management")
    st.markdown("---")

    # Increase tab label size for better readability
    st.markdown(
        """
        <style>
        div[data-baseweb="tab-list"] button p {
            font-size: 1.05rem;
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    # Get database session
    session = next(get_session())
    lesson_service = LessonService(session)
    course_service = CourseService(session)
    theme_service = ThemeService(session)
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Lessons", "Courses", "Themes"])
    
    # ========== LESSONS TAB ==========
    with tab1:
        st.subheader("Lessons")
        
        # Ensure data folders exist
        ensure_data_folders()
        
        # Add new lesson
        with st.expander("➕ Add New Lesson", expanded=False):
            # Audio file upload (required)
            st.markdown("**Audio File (Required)**")
            uploaded_audio = st.file_uploader(
                "Upload MP3 Audio File",
                type=['mp3'],
                key="new_lesson_audio",
                help="Upload the MP3 audio file for this lesson"
            )
            
            auto_duration = None
            duration_detection_error = None
            
            if uploaded_audio is not None:
                st.info(f"**File:** {uploaded_audio.name} | **Size:** {uploaded_audio.size / 1024 / 1024:.2f} MB")
                # Auto-fill filename from uploaded file
                auto_filename = uploaded_audio.name
                # Extract title from filename
                auto_title = extract_title_from_filename(uploaded_audio.name)
                # Extract date from filename
                _, auto_date = extract_date_from_filename(uploaded_audio.name)
                
                # Detect duration using mutagen
                try:
                    audio_data = uploaded_audio.getvalue()
                    audio_info = MP3(BytesIO(audio_data))
                    auto_duration = float(audio_info.info.length)
                except Exception as exc:
                    auto_duration = None
                    duration_detection_error = str(exc)
            else:
                auto_filename = ""
                auto_title = ""
                auto_date = None
                duration_detection_error = None
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Use filename as part of key so widget recreates when file changes
                # This ensures the value updates when a new file is uploaded
                title_key = f"new_lesson_title_{uploaded_audio.name if uploaded_audio else 'none'}"
                new_title = st.text_input(
                    "Title", 
                    value=auto_title if uploaded_audio else "",
                    key=title_key, 
                    help="Title for this lesson (auto-detected from filename)"
                )
                # Filename is auto-filled from upload, display as read-only info
                if uploaded_audio:
                    st.text_input(
                        "Filename (from upload)", 
                        value=auto_filename,
                        key="new_lesson_filename_display", 
                        disabled=True,
                        help="Filename is automatically set from the uploaded file"
                    )
                else:
                    st.info("📁 Upload a file to set the filename")
            
            with col2:
                courses = course_service.get_all_courses()
                course_options = ["None"] + [f"{c.id}: {c.name}" for c in courses]
                new_course = st.selectbox("Course", course_options, key="new_lesson_course")
                new_course_id = None
                if new_course != "None":
                    new_course_id = int(new_course.split(":")[0])
                
                # Use detected date if available, otherwise use today
                # Use filename as part of key so widget recreates when file changes
                date_key = f"new_lesson_date_{uploaded_audio.name if uploaded_audio else 'none'}"
                default_date = auto_date.date() if uploaded_audio and auto_date else datetime.now().date()
                new_date = st.date_input("Date", value=default_date, key=date_key, help="Date (auto-detected from filename if present)")
            
            themes = theme_service.get_all_themes()
            if themes:
                theme_options = [f"{t.id}: {t.name}" for t in themes]
                new_themes = st.multiselect("Themes", theme_options, key="new_lesson_themes")
                new_theme_ids = [int(t.split(":")[0]) for t in new_themes]
            else:
                new_theme_ids = []
                st.info("No themes available. Create themes in the Themes tab.")
            
            # Use filename as part of key so widget recreates when file changes
            duration_key = f"new_lesson_duration_{uploaded_audio.name if uploaded_audio else 'none'}"
            duration_value = auto_duration if auto_duration and auto_duration > 0 else 0.0
            new_duration = st.number_input(
                "Duration (seconds)",
                min_value=0.0,
                value=duration_value,
                step=1.0,
                key=duration_key,
                help="Automatically detected from audio when possible. You can adjust if needed."
            )
            if auto_duration is not None and auto_duration > 0:
                st.caption(f"Detected duration: {auto_duration:.1f} seconds (~{auto_duration/60:.2f} minutes)")
            elif duration_detection_error:
                st.warning("Could not detect audio duration automatically. Please enter it manually.")
            
            if st.button("Create Lesson", key="create_lesson", use_container_width=True):
                if not uploaded_audio:
                    st.error("⚠️ Please upload an MP3 audio file!")
                elif not new_title:
                    st.error("⚠️ Please provide a title!")
                else:
                    try:
                        # Create lesson first to get the ID (keep original filename in DB)
                        lesson = lesson_service.create_lesson(
                            title=new_title,
                            filename=uploaded_audio.name,  # Keep original filename in database
                            course_id=new_course_id,
                            date=datetime.combine(new_date, datetime.min.time()),
                            duration=new_duration if new_duration > 0 else None,
                            theme_ids=new_theme_ids if new_theme_ids else None
                        )
                        
                        # Save audio file with lesson ID prefix for storage (but keep original filename in DB)
                        audio_path = get_audio_file_path(lesson.id, uploaded_audio.name)
                        
                        with open(audio_path, "wb") as f:
                            f.write(uploaded_audio.getbuffer())
                        
                        st.success(f"Lesson '{new_title}' created successfully! Audio file saved.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating lesson: {str(e)}")
                        st.exception(e)
        
        st.markdown("---")
        
        # List and manage lessons
        st.subheader("All Lessons")
        lessons = lesson_service.get_all_lessons()
        
        if lessons:
            # Filter options
            courses = course_service.get_all_courses()
            col1, col2 = st.columns(2)
            with col1:
                filter_course = st.selectbox(
                    "Filter by Course",
                    ["All"] + [f"{c.id}: {c.name}" for c in courses],
                    key="filter_lesson_course"
                )
            with col2:
                search_term = st.text_input("Search by title", key="search_lesson")
            
            # Apply filters
            filtered_lessons = lessons
            if filter_course != "All":
                course_id = int(filter_course.split(":")[0])
                filtered_lessons = [l for l in filtered_lessons if l.course_id == course_id]
            if search_term:
                filtered_lessons = [l for l in filtered_lessons if search_term.lower() in l.title.lower()]
            
            # Display lessons
            for lesson in filtered_lessons:
                with st.expander(f"📄 {lesson.title} - {lesson.date.strftime('%Y-%m-%d')}"):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"**ID:** {lesson.id}")
                        st.write(f"**Course:** {lesson.course.name if lesson.course else 'None'}")
                        st.write(f"**Filename:** {lesson.filename}")
                        st.write(f"**Duration:** {format_duration(lesson.duration)}")
                        
                        # Show themes
                        theme_ids = lesson.get_themes()
                        if theme_ids:
                            theme_objs = theme_service.get_themes_by_ids(theme_ids)
                            theme_names = [t.name for t in theme_objs]
                            st.write(f"**Themes:** {', '.join(theme_names) if theme_names else 'None'}")
                        
                        # Show status
                        status = []
                        if lesson.transcript:
                            status.append("✅ Transcript")
                        if lesson.corrected_transcript:
                            status.append("✅ Corrected")
                        if lesson.summary:
                            status.append("✅ Summary")
                        if status:
                            st.write(f"**Status:** {', '.join(status)}")
                    
                    with col2:
                        if st.button("✏️ Edit", key=f"edit_lesson_{lesson.id}", use_container_width=True):
                            st.session_state[f"editing_lesson_{lesson.id}"] = True
                            st.rerun()
                    
                    with col3:
                        if st.button("🗑️ Delete", key=f"delete_lesson_{lesson.id}", use_container_width=True):
                            lesson_service.delete_lesson(lesson.id)
                            st.success("Lesson deleted!")
                            st.rerun()
                    
                    # Edit form
                    if st.session_state.get(f"editing_lesson_{lesson.id}", False):
                        st.markdown("---")
                        st.markdown("### Edit Lesson")
                        
                        edit_col1, edit_col2 = st.columns(2)
                        
                        with edit_col1:
                            edit_title = st.text_input("Title", value=lesson.title, key=f"edit_title_{lesson.id}")
                            edit_filename = st.text_input("Filename", value=lesson.filename, key=f"edit_filename_{lesson.id}")
                        
                        with edit_col2:
                            edit_courses = course_service.get_all_courses()
                            edit_course_options = ["None"] + [f"{c.id}: {c.name}" for c in edit_courses]
                            current_course = f"{lesson.course_id}: {lesson.course.name}" if lesson.course else "None"
                            edit_course_idx = edit_course_options.index(current_course) if current_course in edit_course_options else 0
                            edit_course = st.selectbox("Course", edit_course_options, index=edit_course_idx, key=f"edit_course_{lesson.id}")
                            edit_course_id = None
                            if edit_course != "None":
                                edit_course_id = int(edit_course.split(":")[0])
                            
                            edit_date = st.date_input("Date", value=lesson.date.date(), key=f"edit_date_{lesson.id}")
                        
                        # Edit themes
                        edit_themes_list = theme_service.get_all_themes()
                        current_theme_ids = lesson.get_themes()
                        if edit_themes_list:
                            current_theme_options = [f"{t.id}: {t.name}" for t in edit_themes_list]
                            current_selected = [f"{t.id}: {t.name}" for t in edit_themes_list if t.id in current_theme_ids]
                            edit_themes = st.multiselect("Themes", current_theme_options, default=current_selected, key=f"edit_themes_{lesson.id}")
                            edit_theme_ids = [int(t.split(":")[0]) for t in edit_themes]
                        else:
                            edit_theme_ids = []
                        
                        edit_duration = st.number_input("Duration (seconds)", min_value=0.0, value=lesson.duration or 0.0, step=1.0, key=f"edit_duration_{lesson.id}")
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.button("💾 Save Changes", key=f"save_lesson_{lesson.id}", use_container_width=True):
                                try:
                                    # Handle file renaming if filename changed
                                    old_audio_path = get_audio_file_path(lesson.id, lesson.filename)
                                    new_filename = edit_filename
                                    
                                    # If filename changed, rename the stored file
                                    if new_filename != lesson.filename:
                                        new_audio_path = get_audio_file_path(lesson.id, new_filename)
                                        
                                        # Rename the file if it exists
                                        if old_audio_path.exists():
                                            old_audio_path.rename(new_audio_path)
                                        elif not new_audio_path.exists():
                                            # If old file doesn't exist, warn
                                            st.warning(f"Original audio file not found. Filename updated in database.")
                                    
                                    # Update lesson with new filename (keep original format in DB)
                                    lesson_service.update_lesson(
                                        lesson.id,
                                        title=edit_title,
                                        filename=new_filename,  # Store original filename in DB
                                        course_id=edit_course_id,
                                        date=datetime.combine(edit_date, datetime.min.time()),
                                        duration=edit_duration if edit_duration > 0 else None,
                                        theme_ids=edit_theme_ids if edit_theme_ids else None
                                    )
                                    st.success("Lesson updated!")
                                    st.session_state[f"editing_lesson_{lesson.id}"] = False
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating lesson: {str(e)}")
                                    st.exception(e)
                        
                        with col_cancel:
                            if st.button("❌ Cancel", key=f"cancel_edit_lesson_{lesson.id}", use_container_width=True):
                                st.session_state[f"editing_lesson_{lesson.id}"] = False
                                st.rerun()
        else:
            st.info("No lessons found. Create your first lesson above.")
    
    # ========== COURSES TAB ==========
    with tab2:
        st.subheader("Courses")
        
        # Add new course
        with st.expander("➕ Add New Course", expanded=False):
            new_course_name = st.text_input("Course Name", key="new_course_name_tab")
            new_course_desc = st.text_area("Description", key="new_course_desc_tab")
            
            if st.button("Create Course", key="create_course_tab", use_container_width=True):
                if new_course_name:
                    try:
                        course_service.create_course(new_course_name, new_course_desc if new_course_desc else None)
                        st.success(f"Course '{new_course_name}' created!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating course: {str(e)}")
                else:
                    st.error("Please provide a course name")
        
        st.markdown("---")
        
        # List and manage courses
        st.subheader("All Courses")
        courses = course_service.get_all_courses()
        
        if courses:
            for idx, course in enumerate(courses):
                with st.expander(f"📚 {course.name}"):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"**ID:** {course.id}")
                        st.write(f"**Description:** {course.description or 'No description'}")
                        
                        # Show lessons in this course
                        course_lessons = lesson_service.get_all_lessons(course_id=course.id)
                        st.write(f"**Lessons:** {len(course_lessons)}")
                        
                        if course_lessons:
                            st.markdown("**Lessons in this course:**")
                            for lesson in course_lessons:
                                st.write(f"- {lesson.title} ({lesson.date.strftime('%Y-%m-%d')})")
                    
                    with col2:
                        if st.button("✏️ Edit", key=f"tab2_edit_course_{course.id}_{idx}", use_container_width=True):
                            st.session_state[f"tab2_editing_course_{course.id}"] = True
                            st.rerun()
                    
                    with col3:
                        if st.button("🗑️ Delete", key=f"tab2_delete_course_{course.id}_{idx}", use_container_width=True):
                            # Check if course has lessons
                            if course_lessons:
                                st.warning(f"Cannot delete course with {len(course_lessons)} lesson(s). Please remove or reassign lessons first.")
                            else:
                                course_service.delete_course(course.id)
                                st.success("Course deleted!")
                                st.rerun()
                    
                    # Edit form
                    if st.session_state.get(f"tab2_editing_course_{course.id}", False):
                        st.markdown("---")
                        st.markdown("### Edit Course")
                        
                        edit_course_name = st.text_input("Course Name", value=course.name, key=f"tab2_edit_course_name_{course.id}")
                        edit_course_desc = st.text_area("Description", value=course.description or "", key=f"tab2_edit_course_desc_{course.id}")
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.button("💾 Save Changes", key=f"tab2_save_course_{course.id}", use_container_width=True):
                                try:
                                    course_service.update_course(course.id, edit_course_name, edit_course_desc if edit_course_desc else None)
                                    st.success("Course updated!")
                                    st.session_state[f"tab2_editing_course_{course.id}"] = False
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating course: {str(e)}")
                        
                        with col_cancel:
                            if st.button("❌ Cancel", key=f"tab2_cancel_edit_course_{course.id}", use_container_width=True):
                                st.session_state[f"tab2_editing_course_{course.id}"] = False
                                st.rerun()
        else:
            st.info("No courses found. Create your first course above.")
    
    # ========== THEMES TAB ==========
    with tab3:
        st.subheader("Themes")
        
        # Add new theme
        with st.expander("➕ Add New Theme", expanded=False):
            new_theme_name = st.text_input("Theme Name", key="new_theme_name_tab")
            
            if st.button("Create Theme", key="create_theme_tab", use_container_width=True):
                if new_theme_name:
                    try:
                        theme_service.create_theme(new_theme_name)
                        st.success(f"Theme '{new_theme_name}' created!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating theme: {str(e)}")
                else:
                    st.error("Please provide a theme name")
        
        st.markdown("---")
        
        # List and manage themes
        st.subheader("All Themes")
        themes = theme_service.get_all_themes()
        
        if themes:
            # Display in grid
            cols = st.columns(3)
            for idx, theme in enumerate(themes):
                with cols[idx % 3]:
                    with st.container():
                        st.markdown(f"### 🏷️ {theme.name}")
                        st.write(f"**ID:** {theme.id}")
                        
                        # Find lessons with this theme
                        all_lessons = lesson_service.get_all_lessons()
                        theme_lessons = [l for l in all_lessons if theme.id in l.get_themes()]
                        st.write(f"**Used in:** {len(theme_lessons)} lesson(s)")
                        
                        if theme_lessons:
                            with st.expander("Lessons with this theme"):
                                for lesson in theme_lessons:
                                    st.write(f"- {lesson.title} ({lesson.date.strftime('%Y-%m-%d')})")
                        
                        col_edit, col_delete = st.columns(2)
                        with col_edit:
                            if st.button("✏️ Edit", key=f"tab3_edit_theme_{theme.id}_{idx}", use_container_width=True):
                                st.session_state[f"tab3_editing_theme_{theme.id}"] = True
                                st.rerun()
                        
                        with col_delete:
                            if st.button("🗑️ Delete", key=f"tab3_delete_theme_{theme.id}_{idx}", use_container_width=True):
                                # Check if theme is used
                                if theme_lessons:
                                    st.warning(f"Cannot delete theme used in {len(theme_lessons)} lesson(s). Please remove theme from lessons first.")
                                else:
                                    theme_service.delete_theme(theme.id)
                                    st.success("Theme deleted!")
                                    st.rerun()
                        
                        # Edit form
                        if st.session_state.get(f"tab3_editing_theme_{theme.id}", False):
                            st.markdown("---")
                            edit_theme_name = st.text_input("Theme Name", value=theme.name, key=f"tab3_edit_theme_name_{theme.id}")
                            
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.button("💾 Save", key=f"tab3_save_theme_{theme.id}", use_container_width=True):
                                    try:
                                        theme_service.update_theme(theme.id, edit_theme_name)
                                        st.success("Theme updated!")
                                        st.session_state[f"tab3_editing_theme_{theme.id}"] = False
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error updating theme: {str(e)}")
                            
                            with col_cancel:
                                if st.button("❌ Cancel", key=f"tab3_cancel_edit_theme_{theme.id}", use_container_width=True):
                                    st.session_state[f"tab3_editing_theme_{theme.id}"] = False
                                    st.rerun()
        else:
            st.info("No themes found. Create your first theme above.")

if __name__ == "__main__":
    app()

