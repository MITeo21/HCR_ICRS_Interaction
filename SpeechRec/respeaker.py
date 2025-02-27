import json
import time
import pyaudio
import numpy as np
import whisper
from vosk import Model, KaldiRecognizer
import torch
from faster_whisper import WhisperModel
import os
import wave

### CONFIGURATION ###
VOSK_MODEL_PATH = r"vosk/vosk-model-en-us-0.22"
WHISPER_MODEL_NAME = "tiny"  # Options: "tiny", "base", "small", "medium", "large"
PAUSE_THRESHOLD = 5 
CHUNK_DIR = "audio_chunks"
TRANSCRIPTION_FILE = "transcriptions.txt"
os.makedirs(CHUNK_DIR, exist_ok=True)  # Ensure directory exists

transcript = []  # Stores transcribed text

# Determine device for Whisper: use GPU (cuda) if available, else fallback to CPU
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Whisper will use device: {device}")

# Initialize Vosk model (for real-time commands)
vosk_model = Model(VOSK_MODEL_PATH)
vosk_recognizer = KaldiRecognizer(vosk_model, 16000)

# Initialize Whisper model (for high-accuracy transcription) on the chosen device
whisper_model = WhisperModel(WHISPER_MODEL_NAME, device=device, compute_type="float16" if device == "cuda" else "int8")

# Find ReSpeaker microphone index
p = pyaudio.PyAudio()
device_index = None
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if "ReSpeaker" in info["name"]:
        device_index = i
        print(f"Using ReSpeaker at index {device_index}")
        break

if device_index is None:
    print("ReSpeaker not found! Using default audio input.")
    device_index = p.get_default_input_device_info()["index"]

# Open microphone stream
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000,
                input=True, frames_per_buffer=2048, input_device_index=device_index)

### FUNCTION TO LISTEN FOR COMMANDS (VOSK) ###
def listen_for_commands():
    print("Listening for commands... (Say 'start note-taking' to activate Whisper)")
    while True:
        data = stream.read(4096, exception_on_overflow=False)
        if vosk_recognizer.AcceptWaveform(data):
            result = json.loads(vosk_recognizer.Result())
            command = result.get("text", "").lower()
            print(f"Recognized command: {command}")

            if "start note-taking" in command:
                print("Switching to Whisper for note-taking...")
                transcribe_speech()  # Call Whisper transcription
                print("Back to command mode...")
                return  # Go back to listening for commands

### FUNCTION TO SAVE AUDIO CHUNKS
def save_audio_chunk(audio_data, chunk_id):
    """Save audio chunk as WAV file."""
    filename = os.path.join(CHUNK_DIR, f"chunk_{chunk_id}.wav")
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(audio_data)
    return filename

### FUNCTION TO SEND AUDIO CHUNKS
def send_audio_chunk():
    # TO DO: can use this function for integration
    pass

### FUNCTION TO SAVE TRANSCRIPTIONS ###
def save_transcription(text):
    with open(TRANSCRIPTION_FILE, "a") as f:
        f.write(text + "\n")

### FUNCTION TO TRANSCRIBE LAB NOTES (WHISPER) ###
def transcribe_speech():
    print("Whisper is now transcribing... (Say 'stop note-taking' to end)")
    audio_data = []
    last_speech_time = time.time()  # Track time of last detected speech
    chunk_id = 0
    
    while True:
        data = stream.read(4096, exception_on_overflow=False)
        audio_data.append(data)

        # Process every ~1 second
        if len(audio_data) > 5:
            raw_audio = b"".join(audio_data)  # Combine buffers
            chunk_filename = save_audio_chunk(raw_audio, chunk_id)
            print(f"Saved chunk: {chunk_filename}")

            # Optionally, send to pipeline (API, queue, processing)
            send_audio_chunk()

            audio_array = np.frombuffer(raw_audio, dtype=np.int16).astype(np.float32) / 32768.0
            segments, _ = whisper_model.transcribe(audio_array)
            text = " ".join(segment.text for segment in segments)

            if text.strip():
                print(f"Transcribed: {text}")

                transcript.append(text)
                print("\r" + text, end="", flush=True)  # Live update

            audio_data = []  # Reset buffer
            chunk_id += 1  # Increment chunk counter

            # Stop transcription when the user says "stop note-taking"
            if "stop note-taking" in text.lower():
                print("Stopping note-taking... Returning to command mode.")
                return  # Exit transcription mode
        
        # Check for silence (no speech for X seconds)
        if time.time() - last_speech_time > PAUSE_THRESHOLD:
            print(f"No speech detected for {PAUSE_THRESHOLD} seconds. Returning to command mode.")
            return  # Exit transcription mode

### MAIN LOOP ###
try:
    while True:
        listen_for_commands()  # Start with Vosk

except KeyboardInterrupt:
    print("Shutting down...")
    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save transcript to file
    if transcript:
        with open("transcript.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(transcript))
        print("\n Transcript saved as 'transcript.txt'.")
    else:
        print("\n No speech detected, transcript not saved.")