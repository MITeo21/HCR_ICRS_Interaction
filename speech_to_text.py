import torch
import pyaudio
import wave
import whisper
from silero_vad import load_silero_vad, get_speech_timestamps
import os
import numpy as np
import torchaudio
import threading
import shutil  # For deleting folders

# Constants for ReSpeaker
FORMAT = pyaudio.paInt16
RESPEAKER_RATE = 16000
RESPEAKER_CHANNELS = 1  # Change based on firmware (1 or 6)
RESPEAKER_WIDTH = 2
RESPEAKER_INDEX = 1  # Input device index (refer to getDeviceInfo.py for the correct index)
CHUNK_SIZE = 1024
CHUNK_DURATION = 10  # Duration of each recorded chunk (seconds)

# Directory paths
WAVE_OUTPUT_DIR = "output_audio_chunks"
# TEMP_DIR = "temp_audio_segments"
TRANSCRIPTION_FILE = os.path.join(WAVE_OUTPUT_DIR, "transcription.txt")

# Load models
USE_ONNX = False  # Set to True if using ONNX
vad_model = load_silero_vad(onnx=USE_ONNX)
whisper_model = whisper.load_model("base")  # Change model if needed


def clean_previous_recordings():
    """Deletes old recordings, temp files, and transcription logs before starting a new session."""
    if os.path.exists(WAVE_OUTPUT_DIR):
        shutil.rmtree(WAVE_OUTPUT_DIR)
    os.makedirs(WAVE_OUTPUT_DIR)

    # if os.path.exists(TEMP_DIR):
    #     shutil.rmtree(TEMP_DIR)
    # os.makedirs(TEMP_DIR)

    open(TRANSCRIPTION_FILE, "w").close()  # Reset transcription file

    print("Previous recordings and temp files cleaned up. Ready to record!")


def process_audio(file_path):
    """Processes recorded audio chunk to extract speech segments."""
    speech_segments = []
    
    # Read audio file
    with wave.open(file_path, 'rb') as wf:
        sample_rate = wf.getframerate()
        num_frames = wf.getnframes()
        audio_data = wf.readframes(num_frames)
    
    # Convert to numpy and tensor
    audio_np = np.frombuffer(audio_data, dtype=np.int16)
    audio_tensor = torch.from_numpy(audio_np).float()
    
    # Get speech timestamps
    speech_timestamps = get_speech_timestamps(audio_tensor, vad_model)

    # Extract speech segments
    for segment in speech_timestamps:
        start = int(segment['start'] / 1000 * sample_rate)
        end = int(segment['end'] / 1000 * sample_rate)
        speech_segments.append(audio_np[start:end])

    return speech_segments


def transcribe_audio(speech_segments):
    """Transcribes speech segments into text using Whisper."""
    transcribed_text = ""

    for idx, segment in enumerate(speech_segments):
        # temp_audio_path = os.path.join(TEMP_DIR, f"temp_segment_{idx}.wav")
        audio_path = os.path.join(WAVE_OUTPUT_DIR, f"chunk{idx}.wav")
        torchaudio.save(audio_path, torch.tensor(segment).unsqueeze(0), RESPEAKER_RATE)

        # Transcribe
        result = whisper_model.transcribe(audio_path)
        transcribed_text += result["text"] + "\n"

    return transcribed_text


def record_audio():
    """Continuously records audio, processes each chunk, and transcribes it in real-time."""
    clean_previous_recordings()  # Clean up old files before starting

    p = pyaudio.PyAudio()
    stream = p.open(
        rate=RESPEAKER_RATE,
        format=p.get_format_from_width(RESPEAKER_WIDTH),
        channels=RESPEAKER_CHANNELS,
        input=True,
        input_device_index=RESPEAKER_INDEX,
    )

    print("* Recording started. Press Ctrl+C to stop.")

    chunk_count = 1
    try:
        while True:
            frames = []
            for _ in range(0, int(RESPEAKER_RATE / CHUNK_SIZE * CHUNK_DURATION)):
                data = stream.read(CHUNK_SIZE)
                frames.append(data)

            output_filename = os.path.join(WAVE_OUTPUT_DIR, f"chunk{chunk_count}.wav")
            with wave.open(output_filename, 'wb') as wf:
                wf.setnchannels(RESPEAKER_CHANNELS)
                wf.setsampwidth(p.get_sample_size(FORMAT))
                wf.setframerate(RESPEAKER_RATE)
                wf.writeframes(b''.join(frames))

            print(f"Saved {output_filename}")

            threading.Thread(target=process_and_transcribe, args=(output_filename,)).start()

            chunk_count += 1

    except KeyboardInterrupt:
        print("\nRecording stopped.")
        cleanup(p, stream)


def process_and_transcribe(file_path):
    """Processes and transcribes a recorded chunk in real-time."""
    print(f"Processing {file_path}...")

    speech_segments = process_audio(file_path)

    if not speech_segments:
        print(f"No speech detected in {file_path}. Skipping transcription.")
        return

    transcribed_text = transcribe_audio(speech_segments)

    with open(TRANSCRIPTION_FILE, "a") as text_file:
        text_file.write(transcribed_text)

    print(f"Transcribed {file_path} and saved results.")


def cleanup(p, stream):
    """Handles cleanup when recording is stopped."""
    stream.stop_stream()
    stream.close()
    p.terminate()

    # # Delete temporary audio files
    # if os.path.exists(TEMP_DIR):
    #     shutil.rmtree(TEMP_DIR)
    #     print("Temporary audio files deleted.")

    print("Cleanup complete. Exiting.")


if __name__ == "__main__":
    record_audio()
