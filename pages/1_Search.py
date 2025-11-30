import streamlit as st
from typing import List, Dict, Tuple
from db.database import get_session
from services.lesson_service import LessonService
from services.course_service import CourseService
import re

# Configure page
st.set_page_config(
    page_title="Search Lessons",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Search Lessons")
st.caption("Search across transcripts, corrected transcripts, and summaries")

# Get database session
session = next(get_session())
lesson_service = LessonService(session)
course_service = CourseService(session)

def highlight_match(text: str, query: str, context_chars: int = 100) -> List[str]:
    """
    Find matches in text and return excerpts with highlighted matches.
    
    Args:
        text: The text to search in
        query: The search query
        context_chars: Number of characters to show before and after match
        
    Returns:
        List of text excerpts containing the match
    """
    if not text or not query:
        return []
    
    # Case-insensitive search
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    matches = []
    
    for match in pattern.finditer(text):
        start = match.start()
        end = match.end()
        
        # Get context around the match
        context_start = max(0, start - context_chars)
        context_end = min(len(text), end + context_chars)
        
        # Extract excerpt
        excerpt = text[context_start:context_end]
        
        # Add ellipsis if not at start/end
        if context_start > 0:
            excerpt = "..." + excerpt
        if context_end < len(text):
            excerpt = excerpt + "..."
        
        # Highlight the match in the excerpt
        # Find the match position in the excerpt
        match_text = text[start:end]
        highlighted = excerpt.replace(match_text, f"**{match_text}**")
        
        matches.append(highlighted)
    
    return matches

def fuzzy_search(text: str, query: str, threshold: float = 0.6) -> bool:
    """
    Simple fuzzy search - checks if query words appear in text.
    
    Args:
        text: Text to search in
        query: Search query
        threshold: Minimum ratio of query words that must match (0.0 to 1.0)
        
    Returns:
        True if text matches query based on threshold
    """
    if not text or not query:
        return False
    
    text_lower = text.lower()
    query_words = query.lower().split()
    
    if not query_words:
        return False
    
    # Count how many query words are found in text
    matches = sum(1 for word in query_words if word in text_lower)
    ratio = matches / len(query_words)
    
    return ratio >= threshold

def search_lessons(query: str, search_transcript: bool, search_corrected: bool, search_summary: bool, fuzzy: bool = True) -> List[Dict]:
    """
    Search lessons based on query and selected scopes.
    
    Args:
        query: Search query
        search_transcript: Whether to search in transcripts
        search_corrected: Whether to search in corrected transcripts
        search_summary: Whether to search in summaries
        fuzzy: Whether to use fuzzy matching
        
    Returns:
        List of dictionaries containing lesson and match information
    """
    results = []
    lessons = lesson_service.get_all_lessons()
    
    for lesson in lessons:
        lesson_result = {
            'lesson': lesson,
            'matches': {},
            'score': 0
        }
        
        # Search in transcript
        if search_transcript and lesson.transcript:
            transcript_text = lesson_service.get_transcript_text(lesson)
            if transcript_text:
                if fuzzy:
                    if fuzzy_search(transcript_text, query):
                        excerpts = highlight_match(transcript_text, query)
                        if excerpts:
                            lesson_result['matches']['transcript'] = excerpts[:3]  # Limit to 3 excerpts
                            lesson_result['score'] += len(excerpts)
                else:
                    excerpts = highlight_match(transcript_text, query)
                    if excerpts:
                        lesson_result['matches']['transcript'] = excerpts[:3]
                        lesson_result['score'] += len(excerpts)
        
        # Search in corrected transcript
        if search_corrected and lesson.corrected_transcript:
            corrected_text = lesson_service.get_corrected_transcript_text(lesson)
            if corrected_text:
                if fuzzy:
                    if fuzzy_search(corrected_text, query):
                        excerpts = highlight_match(corrected_text, query)
                        if excerpts:
                            lesson_result['matches']['corrected'] = excerpts[:3]
                            lesson_result['score'] += len(excerpts)
                else:
                    excerpts = highlight_match(corrected_text, query)
                    if excerpts:
                        lesson_result['matches']['corrected'] = excerpts[:3]
                        lesson_result['score'] += len(excerpts)
        
        # Search in summary
        if search_summary and lesson.summary:
            if fuzzy:
                if fuzzy_search(lesson.summary, query):
                    excerpts = highlight_match(lesson.summary, query)
                    if excerpts:
                        lesson_result['matches']['summary'] = excerpts[:3]
                        lesson_result['score'] += len(excerpts) * 2  # Weight summary matches higher
            else:
                excerpts = highlight_match(lesson.summary, query)
                if excerpts:
                    lesson_result['matches']['summary'] = excerpts[:3]
                    lesson_result['score'] += len(excerpts) * 2
        
        # Only include lessons with matches
        if lesson_result['matches']:
            results.append(lesson_result)
    
    # Sort by score (relevance)
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return results

# Search interface
st.markdown("---")

col1, col2 = st.columns([3, 1])

with col1:
    search_query = st.text_input(
        "Search Query",
        placeholder="Enter search terms...",
        key="search_query",
        help="Enter words or phrases to search for"
    )

with col2:
    fuzzy_mode = st.checkbox(
        "Fuzzy Search",
        value=True,
        help="Match if most query words are found (more flexible)"
    )

# Search scope checkboxes
st.subheader("Search Scope")
col_scope1, col_scope2, col_scope3 = st.columns(3)

with col_scope1:
    search_transcript = st.checkbox("📝 Original Transcript", value=True)

with col_scope2:
    search_corrected = st.checkbox("✅ Corrected Transcript", value=True)

with col_scope3:
    search_summary = st.checkbox("📄 Summary", value=True)

st.markdown("---")

# Search button and results
if st.button("🔍 Search", type="primary", use_container_width=True):
    if not search_query:
        st.warning("⚠️ Please enter a search query")
    elif not (search_transcript or search_corrected or search_summary):
        st.warning("⚠️ Please select at least one search scope")
    else:
        with st.spinner("Searching..."):
            results = search_lessons(
                search_query,
                search_transcript,
                search_corrected,
                search_summary,
                fuzzy_mode
            )
        
        if results:
            st.success(f"✅ Found {len(results)} lesson(s) matching your query")
            
            st.markdown("---")
            
            # Display results
            for i, result in enumerate(results):
                lesson = result['lesson']
                matches = result['matches']
                score = result['score']
                
                # Get course name
                course = course_service.get_course(lesson.course_id) if lesson.course_id else None
                course_name = course.name if course else "No Course"
                
                # Create expandable result
                with st.expander(
                    f"**{i+1}. {lesson.title}** • {lesson.date.strftime('%Y-%m-%d')} • {course_name} • Score: {score}",
                    expanded=(i < 3)  # Expand first 3 results
                ):
                    # Lesson info
                    col_info1, col_info2, col_info3 = st.columns(3)
                    with col_info1:
                        st.caption(f"📅 **Date:** {lesson.date.strftime('%B %d, %Y')}")
                    with col_info2:
                        st.caption(f"📚 **Course:** {course_name}")
                    with col_info3:
                        st.caption(f"🎯 **Relevance:** {score} matches")
                    
                    st.markdown("---")
                    
                    # Display matches by type
                    if 'transcript' in matches:
                        st.markdown("**📝 Original Transcript Matches:**")
                        for excerpt in matches['transcript']:
                            st.markdown(f"• {excerpt}")
                        st.markdown("")
                    
                    if 'corrected' in matches:
                        st.markdown("**✅ Corrected Transcript Matches:**")
                        for excerpt in matches['corrected']:
                            st.markdown(f"• {excerpt}")
                        st.markdown("")
                    
                    if 'summary' in matches:
                        st.markdown("**📄 Summary Matches:**")
                        for excerpt in matches['summary']:
                            st.markdown(f"• {excerpt}")
                        st.markdown("")
                    
                    # Link to lesson
                    st.markdown("---")
                    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
                    with col_btn1:
                        if st.button("📖 View Lesson", key=f"view_lesson_{lesson.id}"):
                            st.session_state['selected_lesson_id'] = lesson.id
                            st.switch_page("Home.py")
                    with col_btn2:
                        if st.button("🔧 Process", key=f"process_lesson_{lesson.id}"):
                            st.session_state['selected_lesson_id'] = lesson.id
                            st.switch_page("pages/Process.py")
        else:
            st.info(f"ℹ️ No lessons found matching '{search_query}'")
            st.markdown("**Suggestions:**")
            st.markdown("- Try different search terms")
            st.markdown("- Enable fuzzy search for more flexible matching")
            st.markdown("- Check more search scopes")
            st.markdown("- Make sure your lessons have content in the selected scopes")

# Show search statistics
st.markdown("---")
st.subheader("📊 Search Statistics")

all_lessons = lesson_service.get_all_lessons()
total_lessons = len(all_lessons)
with_transcript = sum(1 for l in all_lessons if l.transcript)
with_corrected = sum(1 for l in all_lessons if l.corrected_transcript)
with_summary = sum(1 for l in all_lessons if l.summary)

col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)

with col_stat1:
    st.metric("Total Lessons", total_lessons)

with col_stat2:
    st.metric("With Transcript", with_transcript)

with col_stat3:
    st.metric("With Correction", with_corrected)

with col_stat4:
    st.metric("With Summary", with_summary)

