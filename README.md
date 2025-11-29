# Audio Transcription & Analysis App

A Streamlit application for transcribing MP3 audio files using Whisper, correcting transcriptions with LLM, and generating summaries.

## Features

- 🎙️ **Transcribe**: Upload MP3 files and transcribe them using OpenAI Whisper
- ✏️ **Correct**: Improve transcriptions using LLM (OpenAI, Anthropic, or Local)
- 📝 **Summarize**: Generate summaries from original or corrected transcripts
- 🔧 **Prompts**: Manage custom prompts for correction and summarization
- ⚙️ **Setup**: Configure API keys, courses, and themes

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
   - On Windows, if file watching doesn't work, try: `streamlit run app.py --server.runOnSave true`
   - You can also manually trigger a reload by clicking the "Always rerun" button in the Streamlit UI (top right)

2. Navigate to the **Setup** page to:
   - Configure your API keys
   - Create courses and themes

3. Upload an audio file in the **Transcribe** page

4. Use **Correct** to improve transcriptions with LLM

5. Generate summaries in the **Summarize** page

## Folder Structure

```
.
├── app.py                 # Main Streamlit app
├── pages/                 # Frontend pages (Streamlit UI)
│   ├── home.py
│   ├── transcribe.py
│   ├── correct.py
│   ├── summarize.py
│   ├── prompts.py
│   └── setup.py
├── db/                    # Database layer
│   ├── database.py       # Database connection
│   ├── models.py         # SQLModel models
│   └── crud.py           # CRUD operations
├── services/              # Business logic layer
│   ├── lesson_service.py
│   ├── course_service.py
│   └── theme_service.py
├── utils/                 # Utility modules
│   ├── whisper_transcriber.py
│   ├── llm_corrector.py
│   ├── llm_summarizer.py
│   └── file_manager.py
├── data/                  # Data storage
│   ├── audio/            # Uploaded MP3 files (only audio files stored here)
│   ├── prompts/          # Custom prompts
│   └── app.db            # SQLite database (created automatically)
├── setup.yaml            # Configuration file
└── requirements.txt      # Python dependencies
```

## Architecture

The application follows a layered architecture to facilitate migration to a full-stack app:

- **Frontend (pages/)**: Streamlit UI pages - can be replaced with Vue.js
- **Services (services/)**: Business logic layer - reusable in FastAPI backend
- **Database (db/)**: Data access layer with SQLModel - compatible with FastAPI
- **Utils (utils/)**: Utility functions for transcription and LLM operations

## Data Model

- **Lessons**: Store transcriptions, corrections, and summaries
  - Fields: id, title, date, course_id, themes (JSON array), filename, duration, transcript (JSON), corrected_transcript (JSON), summary
- **Courses**: Organize lessons into courses
  - Fields: id, name, description
- **Themes**: Tag lessons with themes (many-to-many via JSON array)
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

## Notes

- Whisper models are downloaded automatically on first use
- Larger Whisper models (medium, large) provide better accuracy but are slower
- Make sure you have sufficient disk space for Whisper models
- Only audio files are stored in the file system; all other data (transcripts, summaries) are stored in the SQLite database
