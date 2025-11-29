# Knowledge Refinery

A Streamlit application for transforming raw audio lessons into refined knowledge: transcribe MP3 audio files using Whisper, correct transcriptions with LLM, and generate insightful summaries with LLM.

## Features

- 📚 **Home**: Browse and explore processed lessons with summaries and transcripts
- 📖 **Lessons**: Manage lessons, courses, and themes with rich metadata
- 🔧 **Process**: Complete workflow for transcription, correction, and summarization
  - 🎙️ **Transcribe**: Convert audio to text using OpenAI Whisper (large-v3)
  - ✏️ **Correct**: Refine transcriptions using LLM (OpenAI or Anthropic)
  - 📝 **Summarize**: Generate concise summaries from transcripts
- ⚙️ **Setup**: Configure API keys, models, and processing parameters

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install FFmpeg (required for Whisper):
   - **Windows**: Download from [FFmpeg website](https://ffmpeg.org/download.html) or use `choco install ffmpeg`
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg`

## Usage

1. Run the Streamlit app:
```bash
streamlit run Home.py
```

   **Note**: The app is configured to auto-reload when you make code changes. If auto-reload doesn't work:
   - Make sure you're not running with `--no-reload` flag
   - On Windows, if file watching doesn't work, try: `streamlit run Home.py --server.runOnSave true`
   - You can also manually trigger a reload by clicking the "Always rerun" button in the Streamlit UI (top right)

2. Navigate to the **Setup** page to configure:
   - API keys for LLM providers (OpenAI/Anthropic)
   - Whisper model settings (model size, device, compute type)
   - Default parameters for transcription, correction, and summarization

3. Create courses and themes in the **Lessons** page

4. Upload audio lessons and process them in the **Process** page

5. Browse completed lessons, summaries, and transcripts in the **Home** page

## Folder Structure

```
knowledge-refinery/
├── Home.py                # Main Streamlit app entry point
├── pages/                 # Frontend pages (Streamlit UI)
│   ├── Lessons_&_courses.py  # Manage lessons, courses, themes
│   ├── Process.py            # Transcribe, correct, summarize workflow
│   └── Setup.py              # Configuration settings
├── db/                    # Database layer
│   ├── database.py       # Database connection and initialization
│   ├── models.py         # SQLModel models (Lesson, Course, Theme)
│   └── crud.py           # CRUD operations
├── services/              # Business logic layer
│   ├── lesson_service.py # Lesson business logic
│   ├── course_service.py # Course business logic
│   └── theme_service.py  # Theme business logic
├── utils/                 # Utility modules
│   ├── whisper_transcriber.py  # Whisper transcription with lazy loading
│   ├── llm_corrector.py        # LLM-based correction
│   ├── llm_summarizer.py       # LLM-based summarization
│   ├── file_manager.py         # File operations and metadata extraction
│   └── background_tasks.py     # Background task management
├── data/                  # Data storage
│   ├── audio/            # Uploaded MP3 files (stored as {id}_{filename})
│   └── app.db            # SQLite database (created automatically)
├── .streamlit/           # Streamlit configuration
│   └── config.toml       # Streamlit settings
├── setup.yaml            # Application configuration
└── requirements.txt      # Python dependencies
```

## Architecture

The application follows a layered architecture to facilitate migration to a full-stack app:

- **Frontend (pages/)**: Streamlit UI pages - can be replaced with Vue.js
- **Services (services/)**: Business logic layer - reusable in FastAPI backend
- **Database (db/)**: Data access layer with SQLModel - compatible with FastAPI
- **Utils (utils/)**: Utility functions for transcription and LLM operations

## Data Model

- **Lessons**: Core entity storing all lesson data and processing results
  - Fields: id, title, date, course_id, themes (JSON array), filename, duration
  - Transcription: transcript (JSON segments), transcript_metadata (JSON)
  - Correction: corrected_transcript (JSON/text), correction_metadata (JSON)
  - Summary: summary (text), summary_metadata (JSON)
  - Metadata includes: provider, model, temperature, prompts, and processing parameters
- **Courses**: Organize lessons into structured courses
  - Fields: id, name, description
- **Themes**: Tag lessons with thematic categories (many-to-many via JSON array)
  - Fields: id, name

## Configuration

Edit `setup.yaml` or use the **Setup** page in the app to configure:
- API keys for LLM providers
- Default models and settings
- File paths and preferences

## Requirements

- Python 3.8+
- FFmpeg
- API key for OpenAI or Anthropic (for correction and summarization)

## Key Features

### Intelligent Processing
- **Lazy Loading**: Whisper model loads only when needed and stays cached for performance
- **Background Tasks**: Long-running processes (transcription, correction, summarization) run in background threads
- **Metadata Tracking**: All processing parameters are stored with results for reproducibility

### Smart File Management
- **Auto-Detection**: Lesson titles and dates extracted automatically from filenames
- **Conflict Prevention**: Audio files stored with unique IDs to prevent naming conflicts
- **Duration Calculation**: Audio file duration automatically calculated on upload

### Flexible Configuration
- **Centralized Settings**: All processing parameters configurable via `setup.yaml` or Setup page
- **Multiple LLM Providers**: Support for OpenAI and Anthropic
- **Customizable Prompts**: Define custom prompts for correction and summarization

## Notes

- Whisper models are downloaded automatically on first use (large-v3 by default)
- Make sure you have sufficient disk space for Whisper models (~3GB for large-v3)
- GPU recommended for faster transcription (CUDA support)
- Only audio files are stored in the file system; all other data (transcripts, summaries, metadata) are stored in the SQLite database
- The app uses Streamlit's native page navigation for optimal auto-reload behavior
