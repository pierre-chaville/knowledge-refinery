import streamlit as st
import time
import yaml
from pathlib import Path
from utils.whisper_transcriber import transcribe_audio
from utils.llm_corrector import correct_transcript
from utils.llm_summarizer import summarize_text
from utils.file_manager import ensure_data_folders, get_audio_file_path
from utils.background_tasks import BackgroundTaskManager
from db.database import get_session
from services.lesson_service import LessonService
from services.theme_service import ThemeService

def load_config():
    """Load configuration from setup.yaml"""
    config_file = Path("setup.yaml")
    if config_file.exists():
        with open(config_file, "r") as f:
            return yaml.safe_load(f) or {}
    return {}

def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "Not set"
    try:
        total = max(0.0, float(seconds))
    except (TypeError, ValueError):
        return "Not set"
    minutes = int(total // 60)
    secs = int(total % 60)
    return f"{minutes:02d}:{secs:02d} ({total:.1f} s)"

def format_timestamp(seconds: float) -> str:
    """Format seconds to HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def format_transcript_with_timestamps(segments: list) -> str:
    """Format transcript segments with timestamps"""
    lines = []
    for seg in segments:
        start = format_timestamp(seg["start"])
        end = format_timestamp(seg["end"])
        text = seg["text"].strip()
        lines.append(f"[{start} - {end}] {text}")
    return "\n".join(lines)

def load_api_key():
    """Load API key from config file if not in session state"""
    if 'api_key' not in st.session_state or not st.session_state.get('api_key'):
        config_file = Path("setup.yaml")
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    config = yaml.safe_load(f) or {}
                    api_key = config.get("api_key", "")
                    if api_key:
                        st.session_state['api_key'] = api_key
            except Exception:
                pass

def app():
    st.title("🎙️ Process Lesson")
    st.markdown("---")
    
    # Ensure data folders exist
    ensure_data_folders()
    
    # Load API key from config if not in session state
    load_api_key()
    
    # Get database session
    session = next(get_session())
    lesson_service = LessonService(session)
    theme_service = ThemeService(session)
    
    # Initialize background task manager
    task_manager = BackgroundTaskManager()
    
    # Initialize session state for selected lesson
    if 'selected_lesson_id' not in st.session_state:
        st.session_state['selected_lesson_id'] = None
    
    # Get all lessons
    lessons = lesson_service.get_all_lessons()
    
    if not lessons:
        st.info("No lessons found. Please create a lesson with an audio file first in the Lessons page.")
        return
    
    # ========== SIDEBAR LESSON SELECTOR ==========
    with st.sidebar:
        st.header("Select Lesson")
        
        # Lesson selection
        lesson_options = []
        for lesson in lessons:
            status_parts = []
            if lesson.transcript:
                status_parts.append("📝")
            if lesson.corrected_transcript:
                status_parts.append("✏️")
            if lesson.summary:
                status_parts.append("📄")
            status = " ".join(status_parts) if status_parts else "⏳"
            lesson_options.append(f"{lesson.id}: {lesson.title} ({lesson.date.strftime('%Y-%m-%d')}) {status}")
        
        selected_lesson_str = st.selectbox(
            "Choose a lesson",
            lesson_options,
            index=0 if st.session_state.get('selected_lesson_id') is None else None,
            help="Select a lesson to process",
            label_visibility="collapsed"
        )
        
        if selected_lesson_str:
            lesson_id = int(selected_lesson_str.split(":")[0])
            st.session_state['selected_lesson_id'] = lesson_id
        
        # Duplicate lesson button
        if st.session_state.get('selected_lesson_id'):
            st.markdown("---")
            st.subheader("Actions")
            
            if st.button("📋 Duplicate Lesson", use_container_width=True, help="Create a copy of this lesson for testing different parameters"):
                lesson_to_duplicate = lesson_service.get_lesson(st.session_state['selected_lesson_id'])
                if lesson_to_duplicate:
                    with st.spinner("Duplicating lesson and audio file..."):
                        new_lesson = lesson_service.duplicate_lesson(st.session_state['selected_lesson_id'])
                        if new_lesson:
                            st.success(f"✅ Lesson duplicated successfully! New lesson ID: {new_lesson.id}")
                            st.info(f"📝 New title: {new_lesson.title}")
                            # Auto-select the new lesson
                            st.session_state['selected_lesson_id'] = new_lesson.id
                            st.rerun()
                        else:
                            st.error("❌ Failed to duplicate lesson")
                else:
                    st.error("❌ Lesson not found")
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Lesson", "🎙️ Transcribe", "✅ Correct", "📄 Summarize"])
    
    # ========== LESSON TAB ==========
    with tab1:
        st.subheader("Lesson Details")
        
        if not st.session_state.get('selected_lesson_id'):
            st.info("👈 Please select a lesson from the sidebar.")
        else:
            lesson_id = st.session_state['selected_lesson_id']
            lesson = lesson_service.get_lesson(lesson_id)
            
            if lesson:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**ID:** {lesson.id}")
                    st.write(f"**Title:** {lesson.title}")
                    st.write(f"**Date:** {lesson.date.strftime('%Y-%m-%d')}")
                    st.write(f"**Course:** {lesson.course.name if lesson.course else 'None'}")
                    st.write(f"**Filename:** {lesson.filename}")
                    st.write(f"**Duration:** {format_duration(lesson.duration)}")
                
                with col2:
                    # Show themes
                    theme_ids = lesson.get_themes()
                    if theme_ids:
                        theme_objs = theme_service.get_themes_by_ids(theme_ids)
                        theme_names = [t.name for t in theme_objs]
                        st.write(f"**Themes:** {', '.join(theme_names)}")
                    
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
                    else:
                        st.write("**Status:** ⏳ Pending")
                    
                    # Check audio file
                    audio_path = get_audio_file_path(lesson.id, lesson.filename)
                    if audio_path.exists():
                        file_size = audio_path.stat().st_size / 1024 / 1024
                        st.success(f"✅ Audio file found ({file_size:.2f} MB)")
                    else:
                        st.error(f"❌ Audio file not found")
                
                # Show transcript if available
                if lesson.transcript:
                    st.markdown("---")
                    st.subheader("Original Transcript")
                    segments = lesson_service.get_transcript_segments(lesson)
                    if segments:
                        transcript_text = format_transcript_with_timestamps(segments)
                    else:
                        transcript_text = lesson_service.get_transcript_text(lesson)
                    st.text_area("Transcript", transcript_text or "", height=200, key=f"lesson_transcript_display_{lesson.id}", disabled=True)
                
                # Show corrected transcript if available
                if lesson.corrected_transcript:
                    st.markdown("---")
                    st.subheader("Corrected Transcript")
                    corrected_text = lesson_service.get_corrected_transcript_text(lesson)
                    st.text_area("Corrected Transcript", corrected_text or "", height=200, key=f"lesson_corrected_display_{lesson.id}", disabled=True)
                
                # Show summary if available
                if lesson.summary:
                    st.markdown("---")
                    st.subheader("Summary")
                    st.markdown(lesson.summary or "")
    
    # ========== TRANSCRIBE TAB ==========
    with tab2:
        st.subheader("Transcribe Audio")
        
        if not st.session_state.get('selected_lesson_id'):
            st.warning("⚠️ Please select a lesson in the 'Lesson' tab first.")
        else:
            lesson_id = st.session_state['selected_lesson_id']
            lesson = lesson_service.get_lesson(lesson_id)
            
            if lesson:
                # Display lesson info
                st.info(f"**Lesson:** {lesson.title} | **File:** {lesson.filename}")
                
                # Check audio file
                audio_path = get_audio_file_path(lesson.id, lesson.filename)
                
                if not audio_path.exists():
                    st.error(f"❌ Audio file not found at: {audio_path}")
                    st.stop()
                
                # Show existing transcript if any
                if lesson.transcript:
                    st.markdown("---")
                    st.subheader("Existing Transcript")
                    
                    # Display metadata
                    metadata = lesson.get_transcript_metadata()
                    if metadata:
                        col_meta1, col_meta2, col_meta3, col_meta4 = st.columns(4)
                        with col_meta1:
                            st.caption(f"**Model:** {metadata.model_size or 'N/A'}")
                        with col_meta2:
                            st.caption(f"**Language:** {metadata.language or 'auto'}")
                        with col_meta3:
                            st.caption(f"**Beam Size:** {metadata.beam_size or 'N/A'}")
                        with col_meta4:
                            st.caption(f"**VAD Filter:** {'Yes' if metadata.vad_filter else 'No'}")
                        if metadata.initial_prompt:
                            with st.expander("View Initial Prompt Used"):
                                st.text(metadata.initial_prompt)
                    
                    existing_transcript = lesson_service.get_transcript_text(lesson)
                    st.text_area(
                        "Current Transcript",
                        existing_transcript or "",
                        height=200,
                        key=f"existing_transcript_tab2_{lesson.id}",
                        disabled=True
                    )
                    st.warning("⚠️ This will replace the existing transcript if you proceed.")
                
                st.markdown("---")
                
                # Display transcription settings from config
                st.subheader("Transcription Settings")
                
                # Load settings from setup.yaml
                config_file = Path("setup.yaml")
                config = {}
                if config_file.exists():
                    with open(config_file, "r") as f:
                        config = yaml.safe_load(f) or {}
                
                whisper_config = config.get("whisper", {})
                transcribe_config = config.get("transcribe", {})
                
                st.info(
                    f"**Model:** {whisper_config.get('model_size', 'large-v3')} | "
                    f"**Device:** {whisper_config.get('device', 'cuda')} | "
                    f"**Language:** {transcribe_config.get('language', 'auto')} | "
                    f"**Beam Size:** {transcribe_config.get('beam_size', 5)} | "
                    f"**VAD Filter:** {'Yes' if transcribe_config.get('vad_filter', True) else 'No'}"
                )
                
                if transcribe_config.get('initial_prompt'):
                    with st.expander("View Initial Prompt"):
                        st.text(transcribe_config['initial_prompt'])
                
                st.caption("💡 Configure default settings in the **Setup** page → **Transcribe** tab.")
                
                # Check for running or completed transcription task
                transcribe_task_id = f"transcribe_{lesson.id}"
                
                if task_manager.is_running(transcribe_task_id):
                    st.info("🔄 Transcription in progress... This page will auto-refresh when complete.")
                    st.markdown("**Status:** Processing audio file...")
                    # Auto-refresh to check for completion
                    time.sleep(2)
                    st.rerun()
                elif task_manager.is_complete(transcribe_task_id):
                    error = task_manager.get_error(transcribe_task_id)
                    if error:
                        st.error(f"Error during transcription: {error}")
                        task_manager.clear_task(transcribe_task_id)
                    else:
                        segments = task_manager.get_result(transcribe_task_id)
                        if segments:
                            st.success("✅ Transcription completed!")
                            
                            # Display transcript with timestamps
                            st.markdown("---")
                            st.subheader("Transcript")
                            transcript_text = format_transcript_with_timestamps(segments)
                            st.text_area(
                                "Transcription Result",
                                transcript_text,
                                height=300,
                                key=f"transcript_result_tab2_{lesson.id}"
                            )
                            
                            # Download button
                            st.download_button(
                                label="📥 Download Transcript",
                                data=transcript_text,
                                file_name=f"{lesson.title}_transcript.txt",
                                mime="text/plain",
                                key="download_transcript_tab2"
                            )
                            
                            task_manager.clear_task(transcribe_task_id)
                
                if st.button("🚀 Start Transcription", type="primary", use_container_width=True, key="transcribe_button"):
                    if task_manager.is_running(transcribe_task_id):
                        st.warning("Transcription already in progress. Please wait.")
                    else:
                        # Load settings from config
                        config_loaded = load_config()
                        transcribe_config = config_loaded.get("transcribe", {})
                        
                        # Capture values before starting thread to avoid ScriptRunContext issues
                        audio_path_captured = str(audio_path)
                        language_captured = transcribe_config.get("language", "auto")
                        if language_captured == "auto":
                            language_captured = None
                        beam_size_captured = transcribe_config.get("beam_size", 5)
                        vad_filter_captured = transcribe_config.get("vad_filter", True)
                        initial_prompt_captured = transcribe_config.get("initial_prompt")
                        lesson_id_captured = lesson.id
                        
                        # Start background transcription
                        def transcribe_task():
                            segments, metadata = transcribe_audio(
                                audio_path_captured,
                                language=language_captured,
                                beam_size=beam_size_captured,
                                vad_filter=vad_filter_captured,
                                initial_prompt=initial_prompt_captured
                            )
                            # Save transcript segments to lesson with metadata
                            lesson_service.save_transcript(
                                lesson_id_captured, 
                                segments,
                                **metadata
                            )
                            return segments
                        
                        task_manager.run_task(transcribe_task_id, transcribe_task)
                        st.rerun()
    
    # ========== CORRECT TAB ==========
    with tab3:
        st.subheader("Correct Transcription")
        
        if not st.session_state.get('selected_lesson_id'):
            st.warning("⚠️ Please select a lesson in the 'Lesson' tab first.")
        else:
            lesson_id = st.session_state['selected_lesson_id']
            lesson = lesson_service.get_lesson(lesson_id)
            
            if lesson:
                # Check if lesson has transcript
                if not lesson.transcript:
                    st.warning("⚠️ This lesson doesn't have a transcript yet. Please transcribe it first in the 'Transcribe' tab.")
                else:
                    transcript_text = lesson_service.get_transcript_text(lesson)
                    
                    st.info(f"**Lesson:** {lesson.title}")
                    
                    st.text_area(
                        "Original Transcript",
                        transcript_text,
                        height=300,
                        key=f"original_transcript_tab3_{lesson.id}"
                    )
                    
                    st.markdown("---")
                    
                    # Display correction settings from config
                    st.subheader("Correction Settings")
                    
                    # Load settings from setup.yaml
                    config_loaded = load_config()
                    correction_config = config_loaded.get("correction", {})
                    
                    st.info(
                        f"**Provider:** {correction_config.get('provider', 'OpenAI')} | "
                        f"**Model:** {correction_config.get('model', 'gpt-4o')} | "
                        f"**Temperature:** {correction_config.get('temperature', 0.3)}"
                    )
                    
                    if correction_config.get('prompt'):
                        with st.expander("View Correction Prompt"):
                            st.text(correction_config['prompt'])
                    
                    st.caption("💡 Configure default settings in the **Setup** page → **Correction** tab.")
                    
                    # Show existing corrected transcript if any
                    if lesson.corrected_transcript:
                        st.markdown("---")
                        st.subheader("Existing Corrected Transcript")
                        
                        # Display metadata
                        metadata = lesson.get_correction_metadata()
                        if metadata:
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
                        
                        existing_corrected = lesson_service.get_corrected_transcript_text(lesson)
                        st.text_area(
                            "Current Corrected Transcript",
                            existing_corrected or "",
                            height=200,
                            key=f"existing_corrected_tab3_{lesson.id}",
                            disabled=True
                        )
                        st.warning("⚠️ This will replace the existing corrected transcript if you proceed.")
                    
                    # Check for running or completed correction task
                    correct_task_id = f"correct_{lesson.id}"
                    
                    if task_manager.is_running(correct_task_id):
                        st.info("🔄 Correction in progress... This page will auto-refresh when complete.")
                        st.markdown("**Status:** Correcting transcript using LLM...")
                        # Auto-refresh to check for completion
                        time.sleep(2)
                        st.rerun()
                    elif task_manager.is_complete(correct_task_id):
                        error = task_manager.get_error(correct_task_id)
                        if error:
                            st.error(f"Error during correction: {error}")
                            task_manager.clear_task(correct_task_id)
                        else:
                            corrected_text = task_manager.get_result(correct_task_id)
                            if corrected_text:
                                st.success("✅ Correction completed!")
                                
                                st.markdown("---")
                                st.subheader("Corrected Transcript")
                                st.text_area(
                                    "Corrected Result",
                                    corrected_text,
                                    height=300,
                                    key=f"corrected_result_tab3_{lesson.id}"
                                )
                                
                                # Download button
                                st.download_button(
                                    label="📥 Download Corrected Transcript",
                                    data=corrected_text,
                                    file_name=f"{lesson.title}_corrected.txt",
                                    mime="text/plain",
                                    key="download_corrected_tab3"
                                )
                                
                                task_manager.clear_task(correct_task_id)
                    
                    if st.button("🔧 Correct Transcript", type="primary", use_container_width=True, key="correct_button"):
                        if task_manager.is_running(correct_task_id):
                            st.warning("Correction already in progress. Please wait.")
                        elif 'api_key' not in st.session_state or not st.session_state.get('api_key'):
                            st.error("⚠️ Please configure your API key in the Setup page first!")
                        else:
                            # Load settings from config
                            config_loaded = load_config()
                            correction_config = config_loaded.get("correction", {})
                            
                            # Capture values before starting thread to avoid ScriptRunContext issues
                            api_key_captured = st.session_state.get('api_key')
                            provider_captured = correction_config.get('provider', 'OpenAI').lower()
                            model_captured = correction_config.get('model', 'gpt-4o')
                            temperature_captured = correction_config.get('temperature', 0.3)
                            prompt_captured = correction_config.get('prompt', 'Please correct any errors in the following transcription, including grammar, punctuation, and factual accuracy. Maintain the original meaning and style.')
                            text_captured = transcript_text
                            lesson_id_captured = lesson.id
                            
                            # Start background correction
                            def correct_task():
                                corrected_text = correct_transcript(
                                    text_captured,
                                    provider=provider_captured,
                                    model=model_captured,
                                    custom_prompt=prompt_captured,
                                    api_key=api_key_captured
                                )
                                # Save corrected transcript to database with metadata
                                lesson_service.save_corrected_transcript(
                                    lesson_id_captured, 
                                    corrected_text,
                                    provider=provider_captured,
                                    model=model_captured,
                                    temperature=temperature_captured,
                                    prompt=prompt_captured
                                )
                                return corrected_text
                            
                            task_manager.run_task(correct_task_id, correct_task)
                            st.rerun()
    
    # ========== SUMMARIZE TAB ==========
    with tab4:
        st.subheader("Summarize Transcript")
        
        if not st.session_state.get('selected_lesson_id'):
            st.warning("⚠️ Please select a lesson in the 'Lesson' tab first.")
        else:
            lesson_id = st.session_state['selected_lesson_id']
            lesson = lesson_service.get_lesson(lesson_id)
            
            if lesson:
                # Choose transcript type
                transcript_type = st.radio(
                    "Transcript Type",
                    ["Original Transcript", "Corrected Transcript"],
                    horizontal=True,
                    key=f"summary_transcript_type_{lesson.id}"
                )
                
                # Get transcript based on type
                if transcript_type == "Original Transcript":
                    if not lesson.transcript:
                        st.warning("⚠️ This lesson doesn't have an original transcript. Please transcribe it first in the 'Transcribe' tab.")
                        st.stop()
                    transcript_text = lesson_service.get_transcript_text(lesson)
                else:
                    if not lesson.corrected_transcript:
                        st.warning("⚠️ This lesson doesn't have a corrected transcript. Please correct it first in the 'Correct' tab.")
                        st.stop()
                    transcript_text = lesson_service.get_corrected_transcript_text(lesson)
                
                st.info(f"**Lesson:** {lesson.title} | **Type:** {transcript_type}")
                
                # Create a unique key based on both lesson ID and transcript type
                transcript_key = "original" if transcript_type == "Original Transcript" else "corrected"
                
                st.text_area(
                    "Transcript to Summarize",
                    transcript_text,
                    height=200,
                    key=f"transcript_to_summarize_tab4_{lesson.id}_{transcript_key}",
                    disabled=True
                )
                
                st.markdown("---")
                
                # Display summary settings from config
                st.subheader("Summary Settings")
                
                # Load settings from setup.yaml
                config_loaded = load_config()
                summary_config = config_loaded.get("summary", {})
                
                st.info(
                    f"**Provider:** {summary_config.get('provider', 'OpenAI')} | "
                    f"**Model:** {summary_config.get('model', 'gpt-4o')} | "
                    f"**Temperature:** {summary_config.get('temperature', 0.7)} | "
                    f"**Type:** {summary_config.get('type', 'concise')} | "
                    f"**Max Length:** {summary_config.get('max_length', 300)} words"
                )
                
                if summary_config.get('prompt'):
                    with st.expander("View Summary Prompt"):
                        st.text(summary_config['prompt'])
                
                st.caption("💡 Configure default settings in the **Setup** page → **Summary** tab.")
                
                # Show existing summary if any
                if lesson.summary:
                    st.markdown("---")
                    st.subheader("Existing Summary")
                    
                    # Display metadata
                    metadata = lesson.get_summary_metadata()
                    if metadata:
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
                
                st.subheader("Current Summary")
                st.markdown(lesson.summary or "")
                st.warning("⚠️ This will replace the existing summary if you proceed.")
                
                # Check for running or completed summary task
                summary_task_id = f"summary_{lesson.id}_{transcript_type}"
                
                if task_manager.is_running(summary_task_id):
                    st.info("🔄 Summary generation in progress... This page will auto-refresh when complete.")
                    st.markdown("**Status:** Generating summary using LLM...")
                    # Auto-refresh to check for completion
                    time.sleep(2)
                    st.rerun()
                elif task_manager.is_complete(summary_task_id):
                    error = task_manager.get_error(summary_task_id)
                    if error:
                        st.error(f"Error during summarization: {error}")
                        task_manager.clear_task(summary_task_id)
                    else:
                        summary_text = task_manager.get_result(summary_task_id)
                        if summary_text:
                            st.success("✅ Summary generated!")
                            
                            st.markdown("---")
                            st.subheader("Summary")
                            st.markdown(summary_text)
                            
                            # Download button
                            st.download_button(
                                label="📥 Download Summary",
                                data=summary_text,
                                file_name=f"{lesson.title}_summary.txt",
                                mime="text/plain",
                                key="download_summary_tab4"
                            )
                            
                            task_manager.clear_task(summary_task_id)
                
                if st.button("📝 Generate Summary", type="primary", use_container_width=True, key="summary_button"):
                    if task_manager.is_running(summary_task_id):
                        st.warning("Summary generation already in progress. Please wait.")
                    elif 'api_key' not in st.session_state or not st.session_state.get('api_key'):
                        st.error("⚠️ Please configure your API key in the Setup page first!")
                    else:
                        # Load settings from config
                        config_loaded = load_config()
                        summary_config = config_loaded.get("summary", {})
                        
                        # Capture values before starting thread to avoid ScriptRunContext issues
                        api_key_captured = st.session_state.get('api_key')
                        provider_captured = summary_config.get('provider', 'OpenAI').lower()
                        model_captured = summary_config.get('model', 'gpt-4o')
                        temperature_captured = summary_config.get('temperature', 0.7)
                        type_captured = summary_config.get('type', 'concise')
                        length_captured = summary_config.get('max_length', 300)
                        prompt_captured = summary_config.get('prompt', 'Please provide a comprehensive summary of the following transcript. Focus on the main points, key insights, and important details.')
                        text_captured = transcript_text
                        lesson_id_captured = lesson.id
                        
                        # Start background summarization
                        def summary_task():
                            summary_text = summarize_text(
                                text_captured,
                                provider=provider_captured,
                                model=model_captured,
                                summary_type=type_captured,
                                max_length=length_captured,
                                custom_prompt=prompt_captured,
                                api_key=api_key_captured
                            )
                            # Save summary to database with metadata
                            lesson_service.save_summary(
                                lesson_id_captured, 
                                summary_text,
                                provider=provider_captured,
                                model=model_captured,
                                temperature=temperature_captured,
                                prompt=prompt_captured
                            )
                            return summary_text
                        
                        task_manager.run_task(summary_task_id, summary_task)
                        st.rerun()

if __name__ == "__main__":
    app()

