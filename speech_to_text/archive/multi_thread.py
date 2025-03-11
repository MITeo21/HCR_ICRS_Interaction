import torch
import pyaudio
import wave
import whisper
from silero_vad import load_silero_vad, get_speech_timestamps
import os
import numpy as np
import torchaudio
import queue
import shutil  
import queue
import threading
import time

# Constants for ReSpeaker
FORMAT = pyaudio.paInt16
RESPEAKER_RATE = 44100  #16000
RESPEAKER_CHANNELS = 1  # Change based on firmware (1 or 6)
RESPEAKER_WIDTH = 2
RESPEAKER_INDEX = 1  # Input device index (refer to getDeviceInfo.py for the correct index)
CHUNK_SIZE = 1024
CHUNK_DURATION = 5  # Duration of each recorded chunk (seconds)

# Directory paths
WAVE_OUTPUT_DIR = "output_audio_chunks"
TRANSCRIPTION_FILE = os.path.join(WAVE_OUTPUT_DIR, "transcription.txt")

# Load models
USE_ONNX = False  # Set to True if using ONNX
vad_model = load_silero_vad(onnx=USE_ONNX)
whisper_model = whisper.load_model("small")  # Change model if needed

# Queue to store audio chunks
audio_queue = queue.Queue()
transcription_queue = queue.Queue()
recording = True


def clean_previous_recordings():
    """Deletes old recordings and transcription logs before starting a new session."""
    if os.path.exists(WAVE_OUTPUT_DIR):
        shutil.rmtree(WAVE_OUTPUT_DIR)
    os.makedirs(WAVE_OUTPUT_DIR)

    open(TRANSCRIPTION_FILE, "w").close()  # Reset transcription file

    print("Previous recordings and temp files cleaned up. Ready to record!")


def record_audio():
    global recording
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=RESPEAKER_CHANNELS,
                        rate=RESPEAKER_RATE, input=True,
                        frames_per_buffer=CHUNK_SIZE)

    while recording:
        frames = []
        for _ in range(0, int(RESPEAKER_RATE / CHUNK_SIZE * CHUNK_DURATION)):
            data = stream.read(CHUNK_SIZE)
            frames.append(data)
        
        # Add chunk to queue
        audio_queue.put(frames)
        print("Chunk added to queue")

    stream.stop_stream()
    stream.close()
    audio.terminate()

def save_audio():
    chunk_count = 0
    while recording or not audio_queue.empty():
        if not audio_queue.empty():
            frames = audio_queue.get()
            filename = f"chunk_{chunk_count}.wav"
            
            # Save chunk
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(RESPEAKER_CHANNELS)
                wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
                wf.setframerate(RESPEAKER_RATE)
                wf.writeframes(b''.join(frames))
            
            print(f"Saved {filename}")
            chunk_count += 1
            
def transcribe_audio():
    """Transcribes audio chunks from the queue and saves the text."""
    while recording or not transcription_queue.empty():
        try:
            audio_file = transcription_queue.get(timeout=1)  # Prevent blocking
            print(f"Transcribing {audio_file}...")

            result = whisper_model.transcribe(audio_file)
            text = result["text"]

            # Save transcription to file
            with open(TRANSCRIPTION_FILE, "a") as f:
                f.write(f"{audio_file}: {text}\n")

            print(f"Transcription saved for {audio_file}: {text}")
        except queue.Empty:
            # Continue checking until recording stops
            pass  


def cleanup(p, stream):
    """Handles cleanup when recording is stopped."""
    stream.stop_stream()
    stream.close()
    p.terminate()

    print("Cleanup complete. Exiting.")
    
    
# Start threads
record_thread = threading.Thread(target=record_audio)
save_thread = threading.Thread(target=save_audio)
transcribe_thread = threading.Thread(target=transcribe_audio)

record_thread.start()
save_thread.start()
transcribe_thread.start()

# Simulate recording for 20 seconds
time.sleep(20)
recording = False

# Wait for threads to finish
record_thread.join()
save_thread.join()
transcribe_thread.join()


# if __name__ == "__main__":
#     #...
