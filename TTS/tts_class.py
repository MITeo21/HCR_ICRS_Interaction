import os
import json
import asyncio
import base64
import websockets
import time
from queue import Queue
from transformers import pipeline
import threading

class TTS:
    def __init__(self, api_key, voice_id, model_id, audio_folder="Visuals/audio"):
        """
        Initialises a TTS Instance.
        
        :param api_key: API key for Eleven Labs
        :param voice_id: Voice ID for the TTS service
        :param model_id: Model ID for speech generation
        :param audio_folder: Folder to store generated audio files
        """
        self.api_key = api_key
        self.voice_id = voice_id
        self.model_id = model_id
        self.audio_folder = audio_folder
        self.speech_queue = Queue()
        self.sentiment_analyser = pipeline("sentiment-analysis")

        ### ensure the audio folder exists
        os.makedirs(self.audio_folder, exist_ok=True)

    async def _generate_speech(self, text):
        """
        Generates speech and adds it to the queue.
        
        :param text: The input text for TTS
        """
        filename = f"speech_{int(time.time() * 1000)}.mp3"
        output_file = os.path.join(self.audio_folder, filename)

        ### EL Websocket URL
        uri = f"wss://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream-input?model_id={self.model_id}"

        async with websockets.connect(uri) as websocket:
            ### send voice settings
            await websocket.send(json.dumps({
                "text": " ",
                "flush": True,
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.8, "use_speaker_boost": False},
                "generation_config": {
                    "chunk_length_schedule": [120, 160, 250, 290]
                },
                "xi_api_key": self.api_key,
            }))

            ### send actual text
            await websocket.send(json.dumps({"text": text}))

            ### indicate end of sequence
            await websocket.send(json.dumps({"text": ""}))

            sentiment = self._analyse_sentiment(text)
            
            ### save the generated speech
            await self._save_audio_from_stream(websocket, output_file, filename, sentiment)

    async def _save_audio_from_stream(self, websocket, output_file, filename, sentiment):
        """
        Saves streamed audio and updates the queue.
        
        :param websocket: The WebSocket connection
        :param output_file: The file path where the audio will be saved
        :param filename: The name of the audio file
        :param sentiment: The sentiment of the speech
        """
        with open(output_file, "wb") as f:
            while True:
                try:
                    ### receiving message
                    message = await websocket.recv()
                    data = json.loads(message)

                    ### decode and write audio data to file
                    if data.get("audio"):
                        f.write(base64.b64decode(data["audio"]))

                    ### if stream is complete, stop listening and update visuals
                    elif data.get("isFinal"):
                        print(f"Audio saved: {output_file}")
                        self.speech_queue.put((filename, sentiment))
                        break

                except websockets.exceptions.ConnectionClosed as e:
                    print(f"Connection closed. Code: {e.code}, Reason: {e.reason}")
                    break
                except Exception as e:
                    print(f"Unexpected error: {e}")
                    break

    def _analyse_sentiment(self, text):
        """
        Analyses the sentiment of the given text.
        
        :param text: The input text
        :return: A sentiment category (positive, negative, or thinking)
        """
        label = self.sentiment_analyser(text)[0]['label']
        if label == "POSITIVE":
            return "positive"
        elif label == "NEGATIVE":
            return "negative"
        else:
            return "thinking"

    async def request_speech_async(self, text):
        """
        Requests speech asynchronously and adds it to the queue.
        
        :param text: The input text
        """
        await self._generate_speech(text)

    def _request_speech_thread(self, text):
        """Runs TTS request asynchronously in a separate thread."""
        asyncio.run(self._generate_speech(text)) 

    def request_speech(self, text):
        """
        Starts a background thread to process TTS request.
        
        :param text: The input text
        """
        thread = threading.Thread(target=self._request_speech_thread, args=(text,))
        thread.start()

    def get_next_speech(self):
        """
        Retrieves the next speech file from the queue, if available.
        
        :return: A tuple containing (filename, sentiment) or None if queue is empty
        """
        return self.speech_queue.get() if not self.speech_queue.empty() else None


# Example Usage
# if __name__ == "__main__":
#     # Initialise TTS Manager
#     tts_manager = TTS(
#         api_key="sk_954ebfba7f0e81b2c0b4aad30f5471321a7ff331b7e93d94",
#         voice_id="ZF6FPAbjXT4488VcRRnw",
#         model_id="eleven_flash_v2_5"
#     )

#     # Test speech generation
#     user_text = input("Enter text for TTS: ")
#     asyncio.run(tts_manager.request_speech_async(user_text))

#     # Retrieve and print speech queue content
#     speech_data = tts_manager.get_next_speech()
#     if speech_data:
#         print(f"Generated Speech: {speech_data[0]}, Sentiment: {speech_data[1]}")
