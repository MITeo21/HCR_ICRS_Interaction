import os
import json
import asyncio
import base64
import websockets
from queue import Queue
import time
from transformers import pipeline

### sentiment analyser
sentiment_analyser = pipeline("sentiment-analysis")

### EL API key
ELEVENLABS_API_KEY = "sk_954ebfba7f0e81b2c0b4aad30f5471321a7ff331b7e93d94"

### set voice and model ID
VOICE_ID = "ZF6FPAbjXT4488VcRRnw"
MODEL_ID = "eleven_flash_v2_5"

### output directory
AUDIO_FOLDER = "Visuals/audio"
os.makedirs(AUDIO_FOLDER, exist_ok=True) # make it if it doesn't exist

### for LLM integration
speech_queue = Queue()

async def text_to_speech_ws_streaming(text):
    """Generates speech and adds it to queue."""
    filename = f"speech_{int(time.time() * 1000)}.mp3"
    output_file = os.path.join(AUDIO_FOLDER, filename)

    ### EL WebSocket URL
    uri = f"wss://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream-input?model_id={MODEL_ID}"

    async with websockets.connect(uri) as websocket:
        ### send voice settings
        await websocket.send(json.dumps({
            "text": " ",
            "flush": True,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.8, "use_speaker_boost": False},
            "generation_config": {
                "chunk_length_schedule": [120, 160, 250, 290]
            },
            "xi_api_key": ELEVENLABS_API_KEY,
        }))

        ### send actual text
        await websocket.send(json.dumps({"text": text}))

        ### indicate end of sequence
        await websocket.send(json.dumps({"text": ""}))

        label = sentiment_analyser(text)[0]['label']

        if label == "POSITIVE":
            sentiment = "positive"
        elif label == "NEGATIVE":
            sentiment = "negative"
        else:
            sentiment = "thinking"

        ### save the generated speech
        await save_audio_from_stream(websocket, output_file, filename, sentiment)

async def save_audio_from_stream(websocket, output_file, filename, sentiment):
    """Save streamed audio and play it with the visuals."""
    with open(output_file, "wb") as f:
        while True:
            try:
                ### receiving message
                message = await websocket.recv()
                data = json.loads(message)

                ### decode and write audio data to file
                if data.get("audio"):
                    print("Writing to file!")
                    f.write(base64.b64decode(data["audio"]))

                ### if stream is complete, stop listening and update visuals
                elif data.get("isFinal"):
                    print(f"Audio saved: {output_file}")
                    speech_queue.put((filename, sentiment))
                    break

            except websockets.exceptions.ConnectionClosed:
                print("Connection closed.")
                break

def request_speech(text):
    """Adds a text request to the speech generation queue."""
    asyncio.run(text_to_speech_ws_streaming(text))

def get_next_speech():
    """Retrieves the next speech file from the queue, if available."""
    return speech_queue.get() if not speech_queue.empty() else None

### test script
if __name__ == "__main__":
    user_text = input("Enter text for TTS: ")
    asyncio.run(text_to_speech_ws_streaming(VOICE_ID, MODEL_ID, user_text))