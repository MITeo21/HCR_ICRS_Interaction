import socket
import threading
import queue


class SpeechRecognitionServer:
    """This class acts as a stand-in for the speech-to-text component, in order to test the LLM's functionality, alone"""
    def __init__(self, host='127.0.0.1', port=13245):
        self.host = host
        self.port = port
        self.query_queue = queue.Queue()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server listening on {self.host}:{self.port}")
        main_handler = threading.Thread(
            target=self.start
        )
        main_handler.start()

    def handle_client(self, client_socket):
        try:
            while True:
                data = client_socket.recv(1024).decode('utf-8').strip()
                if not data:
                    break

                self.query_queue.put(data)
                print(f"Queue is {"" if self.query_queue.empty() else "not "}empty. Received: {data}")
        finally:
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

if __name__ == "__main__":
    server = SpeechRecognitionServer()