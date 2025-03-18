import socket
import os


class TXTClient:
    """This is just a very simple client for communicating with a server"""
    def __init__(self, host=None, port=None):
        self.server_host = (
            os.environ.get('ITTS_HOST', '127.0.0.1')
            if host is None else host
        )
        self.server_port = (
            int(os.environ.get('ITTS_PORT', 13245))
            if port is None else port
        )
        # ^ this line only works if run in same environment as server


    def send_loop(self):
        try:
            while True:
                message = input("Enter message to send: ")
                self.client_socket.sendall(message.encode())
        except KeyboardInterrupt:
            print("\nDisconnecting client...")
            self.client_socket.close()
            exit(0)
        except Exception as e:
            print(f"Error during communication: {e}")
        finally:
            self.client_socket.close()
            exit(1)


    def start(self):
        print(f"Connecting to server at {self.server_host}:{self.server_port}")
        try:
            self.client_socket = socket.create_connection(
                (self.server_host, self.server_port)
            )
            self.send_loop()
        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            self.client_socket.close()


if __name__ == "__main__":
    client = TXTClient()
    client.start()