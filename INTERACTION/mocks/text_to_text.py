import socket
import threading
import queue
import os
from random import random
import asyncio


class InputServer:
    """This class acts as a stand-in for the speech-to-text component, in order to avoid needing to speak queries out loud for testing"""
    def __init__(self, **_):
        # drop any kwargs, only accepted for compatibility

        # set connection parameters from environment variables
        self.host = os.environ.get('ITTS_HOST', '127.0.0.1')
        self.port = int(os.environ.get('ITTS_PORT', 13245))

        self.query_queue = queue.Queue()

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server listening on {self.host}:{self.port}")

        # set up new thread to handle clients
        # to leave main thread free for calls to `text`
        server_thread = threading.Thread(target=self.start)
        server_thread.start()


    def handle_client(self, client_socket):
        try:
            while True:
                data = client_socket.recv(1024).decode('utf-8').strip()
                if not data:
                    break

                self.query_queue.put(data)
        finally:
            print("Client disconnected.")
            client_socket.close()

    def start(self):
        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                print(f"Connection from {addr}")
                client_handler = threading.Thread(
                    target=self.handle_client, args=(client_socket,)
                )
                client_handler.start()
        except KeyboardInterrupt:
            print("\nServer shutting down.")
        finally:
            self.server_socket.close()

    def text(self, handler):
        txt = self.query_queue.get()
        handler(txt)


class TTT:
    """This class acts as a stand-in for the TTS component, to avoid expensive API calls when testing the system"""
    def __init__(self, audio_folder=None, **_):
        # expecting import to be used in interaction.py, called from repo root
        self.audio_folder = (
            os.path.join("..", "..", "..", "INTERACTION", "mocks", "audio")
            if audio_folder is None else audio_folder
        )
        self.speech_queue = queue.Queue()
        self.captions = ""

    async def _generate_speech(self, text):
        """
        Simulates speech generation by adding a dummy audio file to the queue.

        :param text: The input text for TTS
        """
        self.captions = text

        filename = os.path.join(self.audio_folder, "wha-wha.mp3")
        await asyncio.sleep(0.3)

        # Simulate sentiment analysis
        sentiment = "positive" if random() < 0.8 else "negative"

        # Add to queue
        self.speech_queue.put((filename, sentiment))

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
        Processes TTS request by simulating speech generation.

        :param text: The input text
        """
        thread = threading.Thread(
            target=self._request_speech_thread, args=(text,)
        )
        thread.start()

    def get_next_speech(self):
        """
        Retrieves the next speech file from the queue, if available.

        :return: A tuple: (filename, sentiment) or None if queue is empty
        """
        return (
            self.speech_queue.get() if not self.speech_queue.empty() else None,
            self.captions
        )
