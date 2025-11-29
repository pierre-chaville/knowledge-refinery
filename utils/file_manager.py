"""File management utilities"""
from pathlib import Path
import re
from datetime import datetime

def ensure_data_folders():
    """Create data folder structure if it doesn't exist"""
    folders = [
        "data",
        "data/audio",
        "data/prompts",
        "data/prompts/custom"
    ]
    
    for folder in folders:
        Path(folder).mkdir(parents=True, exist_ok=True)

def get_audio_file_path(lesson_id: int, filename: str) -> Path:
    """
    Get the actual file path for an audio file.
    Files are stored as {id}_{filename} but database stores original filename.
    
    Args:
        lesson_id: The lesson ID
        filename: The original filename from database
    
    Returns:
        Path to the actual audio file
    """
    audio_dir = Path("data/audio")
    # Construct the stored filename with ID prefix
    stored_filename = f"{lesson_id}_{filename}"
    return audio_dir / stored_filename

def extract_date_from_filename(filename: str) -> tuple[str, datetime | None]:
    """
    Extract date from filename in YYYYMMDD format.
    Dates can be preceded/followed by underscores or at start/end of string.
    
    Args:
        filename: The filename (with or without extension)
    
    Returns:
        Tuple of (cleaned_filename_without_date, datetime_object or None)
    """
    # Remove extension
    name_without_ext = Path(filename).stem
    
    # Pattern: YYYYMMDD where YYYY is 1900-2099, MM is 01-12, DD is 01-31
    # Match dates that are preceded by underscore or start of string, and followed by underscore or end of string
    date_pattern = r'(?:^|_)((19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01]))(?:_|$)'
    
    match = re.search(date_pattern, name_without_ext)
    if match:
        date_str = match.group(1)  # Get the date part without the underscore
        try:
            # Parse YYYYMMDD format
            date_obj = datetime.strptime(date_str, "%Y%m%d")
            # Remove date from filename (including surrounding underscores)
            cleaned_name = re.sub(date_pattern, '', name_without_ext)
            # Clean up double underscores or trailing/leading underscores
            cleaned_name = re.sub(r'_+', '_', cleaned_name).strip('_')
            return cleaned_name, date_obj
        except ValueError:
            pass
    
    return name_without_ext, None

def extract_title_from_filename(filename: str) -> str:
    """
    Extract a title from filename by:
    - Replacing underscores with spaces
    - Removing date in YYYYMMDD format if present
    - Cleaning up the result
    
    Args:
        filename: The filename (with or without extension)
    
    Returns:
        Suggested title string
    """
    # Remove extension and date
    name_without_ext, _ = extract_date_from_filename(filename)
    
    # Replace underscores with spaces
    title = name_without_ext.replace("_", " ")
    
    # Clean up multiple spaces
    title = re.sub(r'\s+', ' ', title).strip()
    
    # Remove leading/trailing dashes or spaces
    title = title.strip(' -')
    
    # Capitalize first letter of each word if title is meaningful
    if title:
        # Split into words and capitalize each
        words = title.split()
        title = ' '.join(word.capitalize() for word in words)
    
    return title if title else filename
