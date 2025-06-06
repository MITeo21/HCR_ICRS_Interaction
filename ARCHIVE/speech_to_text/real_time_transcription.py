# =============================================================================
# Original code taken from Whisper RealTime on 06-03-2025
# https://github.com/davabase/whisper_real_time/blob/master/transcribe_demo.py
# Bulk modified into class by ChatGPT 4o mini on 06-03-2025
# Updates and fixes for Linux-platform compatibility written by lemon-gith
# Triggering mechanisms written by mk1021 and lemon-gith
# =============================================================================

### THIS CODE IS DEPRECATED CURRENTLY; PLEASE REFER TO INTERACTION.PY FOR CURRENT STT IMPLEMENTATION

import os
import wave
import numpy as np
import speech_recognition as sr
import whisper
import torch
import shutil
import sounddevice  # black magic to make this run on linux

from datetime import datetime, timedelta, UTC
from queue import Queue
from time import sleep


class SpeechToText:
    def __init__(
        self, model="turbo", non_english=False, energy_threshold=1000,
        record_timeout=4.0, phrase_timeout=3.0, transcription_timeout=5.0,
        mic_name="ReSpeaker", dynamic_energy_threshold=False
    ):
        self.model_name = model
        self.non_english = non_english
        self.energy_threshold = energy_threshold
        self.transcription_timeout = transcription_timeout
        self.record_timeout = record_timeout
        self.phrase_timeout = phrase_timeout
        self.mic_name = mic_name  # Default: "ReSpeaker"

        self.phrase_time = None
        self.last_spoken = None
        self.data_queue = Queue()
        self.query_queue = Queue()
        print(f"qsize: {self.query_queue.qsize()}")
        self.transcription = ['']
        self.transcription_file = os.path.join("output", "transcription.txt")
        if not os.path.exists("output"):
            os.makedirs("output")
        self.audio_buffer = []  # Store audio chunks for saving

        # Initialize speech recognizer
        self.recorder = sr.Recognizer()
        self.recorder.energy_threshold = self.energy_threshold
        self.recorder.dynamic_energy_threshold = dynamic_energy_threshold
        self.transcribe = False  # initialise to false

        # Select microphone
        self.source = self.get_microphone()

        # Load Whisper model
        self.load_model()


    def get_microphone(self):
        """Finds and selects the ReSpeaker microphone"""
        mic_index = None
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            if self.mic_name.lower() in name.lower():
                mic_index = index
                break

        if mic_index is None:
            raise ValueError(
                f"Microphone '{self.mic_name}' not found. Run `python -m speech_recognition` to check available devices.\n\n"
                + "When running on Ubuntu, you may need to first run `jack_control start` to enable audio input.\n"
            )

        print(f"Using microphone: {self.mic_name} (index {mic_index})")
        return sr.Microphone(sample_rate=16000, device_index=mic_index)


    def load_model(self):
        """Loads the Whisper speech-to-text model"""
        model = self.model_name
        if (
            model in ["tiny", "base", "small", "medium"]
            and not self.non_english
        ):
            model += ".en"

        self.audio_model = whisper.load_model(model)
        print(f"Whisper model ({model}) loaded.")


    def record_callback(self, _, audio: sr.AudioData):
        """Callback function to store recorded audio chunks"""
        data = audio.get_raw_data()
        self.data_queue.put(data)
        self.audio_buffer.append(data)  # Save audio chunks for later


    def start_listening(self):
        """Starts background listening with the ReSpeaker microphone"""
        with self.source:
            self.recorder.adjust_for_ambient_noise(self.source)

        self.recorder.listen_in_background(
            self.source, self.record_callback,
            phrase_time_limit=self.record_timeout
        )
        print("Listening...")


    def process_audio(self):
        """Processes recorded audio from the queue and transcribes it"""
        while True:
            try:
                now = datetime.now(UTC)

                if not self.data_queue.empty():
                    phrase_complete = False
                    if (self.phrase_time and now - self.phrase_time >
                            timedelta(seconds=self.phrase_timeout)
                    ):
                        phrase_complete = True

                    self.phrase_time = now
                    self.last_spoken = now

                    audio_data = b''.join(self.data_queue.queue)
                    self.data_queue.queue.clear()

                    audio_np = np.frombuffer(
                        audio_data, dtype=np.int16
                    ).astype(np.float32) / 32768.0

                    result = self.audio_model.transcribe(
                        audio_np, fp16=torch.cuda.is_available()
                    )

                    text = result['text'].strip()
                    
                    if "iris" in text.lower() or "harry" in text.lower():
                        self.transcribe = True
                        # can add the robot replying before requesting for something?
                        print("Starting Transcription...")
                    # print(f"phrase_complete: {phrase_complete}")
                    # print(f"self.transcribe: {self.transcribe}")
                    self.query_queue.put(text)
                    if phrase_complete and self.transcribe:
                        # print(text)
                        # self.query_queue.put(text)
                        print(f"qsize: {self.query_queue.qsize()}")
                        # print(self.query_queue.get())
                        self.transcription.append(text)
                        # Save transcription to file

                        with open(self.transcription_file, "a") as f:
                            f.write(f"{text}\n")

                    elif self.transcribe:
                        self.transcription[-1] += text

                    # os.system('cls' if os.name == 'nt' else 'clear')
                    for line in self.transcription:
                        print(line)
                    print('', end='', flush=True)
                elif (self.last_spoken and
                        now - self.last_spoken >
                            timedelta(seconds=self.transcription_timeout)
                ):
                    print(f"This is an implementation for timing out if it receives no new data for a certain amount of time. Please implement what it is that you're planning on using.")
                else:
                    sleep(0.25)
            except KeyboardInterrupt:
                print("\nStopping... Saving audio file.")
                self.save_audio()
                break
            except:
                print("error")



    def save_audio(self):
        """Saves recorded audio to a single WAV file"""
        chunk_count = 0
        if not self.audio_buffer:
            print("No audio recorded.")
            return
        
        filename = os.path.join(
            "output", os.path.basename(__file__) + f"_chunk_{chunk_count}.wav"
        )
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)  # Mono
            wf.setsampwidth(2)  # 16-bit PCM
            wf.setframerate(16000)  # 16kHz sample rate
            wf.writeframes(b''.join(self.audio_buffer))

        print(f"Audio saved as {filename}")
        chunk_count += 1


    def clean_previous_recordings(self):
        """Deletes old recordings and transcription logs before starting a new session."""
        if os.path.exists("output"):
            shutil.rmtree("output")
        os.makedirs("output")

        open(self.transcription_file, "w").close()  # Reset transcription file

        print("Previous recordings and temp files cleaned up. Ready to record!")

    
    def run(self):
        """Runs the full speech recognition process"""
        self.clean_previous_recordings()
        self.start_listening()
        self.process_audio()


if __name__ == "__main__":
    stt = SpeechToText(
        model="turbo", mic_name="MacBook Pro Microphone",
        energy_threshold=2000
    )
    stt.run()
