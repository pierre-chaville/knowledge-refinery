import json
import time
from utils.whisper_transcriber import transcribe_audio

#with open('data/audio/audio.mp3', 'rb') as audio_file:
#transcription = transcribe_audio(audio_file)
print("Starting test transcription...")
start_time = time.time()
transcribe_audio('data/audio/audio.mp3', language='fr')
print(f"Time taken: {time.time() - start_time} seconds, i.e. {(time.time() - start_time) / 60} minutes.")

