"""Whisper transcription utilities"""
import time
import json
import yaml
from pathlib import Path

# Global model cache
_model = None
_model_config = None

def get_whisper_model():
    """
    Get or initialize the Whisper model with lazy loading.
    Model is cached globally to avoid reloading.
    Import is delayed until first use for faster app startup.
    """
    global _model, _model_config
    
    # Load config from setup.yaml
    config_file = Path("setup.yaml")
    config = {}
    if config_file.exists():
        with open(config_file, "r") as f:
            config = yaml.safe_load(f) or {}
    
    # Get whisper config with defaults
    whisper_config = config.get("whisper", {})
    model_size = whisper_config.get("model_size", "large-v3")
    device = whisper_config.get("device", "cuda")
    compute_type = whisper_config.get("compute_type", "int8")
    
    current_config = (model_size, device, compute_type)
    
    # Check if model needs to be (re)loaded
    if _model is None or _model_config != current_config:
        # Import faster_whisper only when actually needed
        from faster_whisper import WhisperModel
        
        print(f"Loading Whisper model {model_size} on {device} with compute type {compute_type}...")
        start_time = time.time()
        _model = WhisperModel(model_size_or_path=model_size, device=device, compute_type=compute_type)
        _model_config = current_config
        print(f"Model loaded in {time.time() - start_time:.2f} seconds")
    
    return _model, model_size, device, compute_type

def transcribe_audio(
    audio_path: str, 
    language: str = None,
    beam_size: int = 5,
    vad_filter: bool = True,
    initial_prompt: str = None
) -> tuple[list, dict]:
    """
    Transcribe audio and return list of segments with timestamps and metadata.
    Model is loaded lazily on first call and cached for subsequent calls.
    
    Returns:
        Tuple of (segments, metadata_dict)
        - segments: List of dicts with keys: 'start', 'end', 'text'
        - metadata_dict: Dict with transcription parameters
    """
    # Get or initialize model
    model, model_size, device, compute_type = get_whisper_model()
    
    start_time = time.time()
    print(f"Starting transcription of {audio_path}...")
    
    # Transcribe audio
    segments, info = model.transcribe(
        audio_path,
        language=language,
        beam_size=beam_size,
        vad_filter=vad_filter,
        initial_prompt=initial_prompt,
    )

    seg_list = []
    for s in segments:
        seg_list.append({
            "start": s.start,
            "end": s.end,
            "text": s.text
        })
    
    print(f"Time taken to transcribe audio: {time.time() - start_time} seconds, i.e. {(time.time() - start_time) / 60} minutes.")
    print(f"Transcribed {len(seg_list)} segments")

    # saving the transcription to a file
    with open(f'data/audio_{model_size}_{device}_{compute_type}.json', 'w') as f:
        json.dump(seg_list, f, indent=4)
    
    # Prepare metadata
    metadata = {
        'model_size': model_size,
        'device': device,
        'compute_type': compute_type,
        'beam_size': beam_size,
        'vad_filter': vad_filter,
        'language': language,
        'initial_prompt': initial_prompt
    }
    
    return seg_list, metadata


