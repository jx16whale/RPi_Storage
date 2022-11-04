"""
Testing Algorithm Socket Only - Not used in production.
"""
import queue
import socket
import threading
from imageProcessingServer.config import FORMAT, ALGO_SOCKET_BUFFER_SIZE, WIFI_IP, WIFI_PORT

class AlgoClient:

    def __init__(self) -> None:
        print("[Algo Client] Initilising Algo Client")
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((WIFI_IP, WIFI_PORT))
        # self.incoming_message_queue = queue.Queue()
        self.message_sender = threading.Thread(target=self.message_sender_thread)
        self.message_receiver = threading.Thread(target=self.message_receiver_thread)
        #self.printer = threading.Thread(target=self.print_messages)
        print("[Algo Client] Algo Client Receiver Thread started")
        self.message_receiver.start()
        print("[Algo Client] Algo Client Sender Thread started")
        self.message_sender.start()
        
    def message_sender_thread(self) -> None:
        # We want to encode into bytes.
        while True:
            try:
                msg = input("[Algo Client] Message to server: ")
                message = msg.encode(FORMAT)
                # Pad to Socket buffer size
                #message += (ALGO_SOCKET_BUFFER_SIZE - len(message)) * b' ' 
                self.client.send(message)
                print(f"[Algo Client] Message Sent: {msg}")
            except Exception as e:
                print(e)

    def message_receiver_thread(self) -> None:
        while True:
            try:
                message = self.client.recv(ALGO_SOCKET_BUFFER_SIZE).decode(FORMAT)
                print(message)
            except Exception as e:
                print(e)

# Standalone testing.
if __name__ == '__main__':
    AlgoClient()