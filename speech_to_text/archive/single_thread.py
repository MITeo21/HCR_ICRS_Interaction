import torch
import pyaudio
import wave
import whisper
from silero_vad import load_silero_vad, read_audio, get_speech_timestamps, save_audio

# Constants for ReSpeaker
RESPEAKER_RATE = 16000
RESPEAKER_CHANNELS = 1  # Change based on firmware (1 or 6)
RESPEAKER_WIDTH = 2
RESPEAKER_INDEX = 1  # Input device index (refer to getDeviceInfo.py for the correct index)
CHUNK = 1024
RECORD_SECONDS = 10
WAVE_OUTPUT_FILENAME = "output.wav"

# Load the Silero VAD model
USE_ONNX = False  # Set to True if you want to use the ONNX model
vad_model = load_silero_vad(onnx=USE_ONNX)

# Load the Whisper model for transcription
whisper_model = whisper.load_model("base")  # You can change "base" to other models like "small", "medium", "large"

def record_audio():
    """
    Records audio using ReSpeaker and saves it to a WAV file.
    """
    p = pyaudio.PyAudio()

    stream = p.open(
        rate=RESPEAKER_RATE,
        format=p.get_format_from_width(RESPEAKER_WIDTH),
        channels=RESPEAKER_CHANNELS,
        input=True,
        input_device_index=RESPEAKER_INDEX,
    )

    print("* recording")

    frames = []

    for i in range(0, int(RESPEAKER_RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("* done recording")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(RESPEAKER_CHANNELS)
    wf.setsampwidth(p.get_sample_size(p.get_format_from_width(RESPEAKER_WIDTH)))
    wf.setframerate(RESPEAKER_RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

def process_audio(audio_file):
    """
    Process the audio file using VAD (Voice Activity Detection) and returns speech segments.
    """
    # Read the audio file
    audio = read_audio(audio_file)

    # Get speech timestamps from the audio
    speech_timestamps = get_speech_timestamps(audio, vad_model)

    # Collect and save the speech segments
    speech_segments = []
    for segment in speech_timestamps:
        start = segment['start'] / 1000  # Convert milliseconds to seconds
        end = segment['end'] / 1000  # Convert milliseconds to seconds
        speech_segment = audio[int(start * 16000):int(end * 16000)]  # Assuming a sample rate of 16000 Hz
        speech_segments.append(speech_segment)

    return speech_segments

def transcribe_audio(speech_segments):
    """
    Transcribe the speech segments into text using Whisper.
    """
    transcribed_text = ""
    for segment in speech_segments:
        # Save the speech segment as a temporary audio file
        temp_audio_path = "temp_segment.wav"
        save_audio(temp_audio_path, segment)

        # Transcribe the segment using Whisper
        result = whisper_model.transcribe(temp_audio_path)
        transcribed_text += result["text"] + "\n"

    return transcribed_text

def speech_to_text():
    # Record audio from the ReSpeaker microphone
    record_audio()

    # Process the recorded audio to get speech segments
    speech_segments = process_audio(WAVE_OUTPUT_FILENAME)

    # Transcribe the speech segments
    transcribed_text = transcribe_audio(speech_segments)

    # Save the transcribed text to a text file
    with open("transcription.txt", "w") as text_file:
        text_file.write(transcribed_text)

    print("Transcription completed! Check 'transcription.txt' for the output.")

if __name__ == "__main__":
    speech_to_text()
