import whisper
import torch
import numpy as np
import pyaudio
import queue
import time
import threading

class SpeechRecognizer:
    def __init__(self, model_size="tiny", silence_threshold=200, silence_timeout=3):
        self.model = whisper.load_model(model_size)
        self.silence_threshold = silence_threshold
        self.silence_timeout = silence_timeout

        self.audio_queue = queue.Queue()
        self.query_queue = queue.Queue()
        self.transcript = []
        self.last_speech_time = None

        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000 
        self.CHUNK = 1024

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
            stream_callback=self._callback
        )

        self.is_recording = threading.Event()
        self.is_recording.clear()
        self.recorded_audio = bytes()

    def _callback(self, in_data, frame_count, time_info, status):
        # audio_data = np.frombuffer(in_data, dtype=np.int16)
        # print(f"Is recording? {self.is_recording.is_set()}")
        if self.is_recording.is_set():
            # print("callback recording")
            # if np.abs(audio_data).mean() > self.silence_threshold:
                # print("callback recording fr")    
            self.last_speech_time = time.time()
            self.audio_queue.put(in_data)
            self.recorded_audio += in_data

        return (None, pyaudio.paContinue)
        

    def _toggle_recording(self):
        if not self.is_recording.is_set():
            self.is_recording.set()
            self.last_speech_time = time.time()
            self.recorded_audio = bytes()
            print("\n Recording Started... Speak now!")
            # while not self.audio_queue.empty():
            #     self.recorded_audio += self.audio_queue.get()
            # audio_buffer = bytes()
            # while self.is_recording:
            #     # Stop if silence detected
            #     if time.time() - self.last_speech_time > self.silence_timeout:
            #         time.sleep(2)
            #         print("\nPaused due to silence.")
            #         break

            #     while not self.audio_queue.empty():
            #         audio_buffer += self.audio_queue.get()

            #     if len(audio_buffer) > self.RATE * 2:
            #         audio_np = np.frombuffer(audio_buffer, dtype=np.int16).astype(np.float32) / 32768.0  # Normalize
            #         result = self.model.transcribe(audio_np, fp16=torch.cuda.is_available())  # Whisper transcription

            #         text = result["text"].strip()
            #         if text:
            #             self.transcript.append(text)
            #             print(f"\r{text}", end="", flush=True)

            #         audio_buffer = bytes()
            
            # self.query_queue.put(" ".join(self.transcript))
        else:
            self.is_recording.clear()
            print("\n Recording stopped...transcribing")
            print(len(self.recorded_audio))
            if len(self.recorded_audio) > self.RATE * 2:
                audio_np = np.frombuffer(self.recorded_audio, dtype=np.int16).astype(np.float32) / 32768.0  # Normalize
                print("line 1")
                # result = self.model.transcribe(audio_np, fp16=torch.cuda.is_available())  # Whisper transcription
                result = self.model.transcribe(audio_np, fp16=False)
                print("line 2")
                
                text = result["text"].strip()
                print("line 3")
                if text:
                    self.transcript.append(text)
                    print(f"\n Transcription: {text}")
                    self.query_queue.put(" ".join(self.transcript))
                    return

            print("No speech detected.")
            # self.cleanup()
            return None
    
    def toggle_recording(self):
        thread = threading.Thread(target=self._toggle_recording)
        thread.start()


    # def stop_recording(self):
    #     self.is_recording = False

    def cleanup(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

    def save_transcript(self, filename="transcript.txt"):
        if self.transcript:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n".join(self.transcript))
            print(f"\n Transcript saved as '{filename}'.")
        else:
            print("\n No speech detected, transcript not saved.")
