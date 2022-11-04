import socket
from commServers.config import ALGO_SOCKET_BUFFER_SIZE, WIFI_PORT, WIFI_IP

class AlgoServer:
    def __init__(self):
        
        self.host = WIFI_IP
        self.port = WIFI_PORT
        
        self.clientsocket = None
        self.address = None
        
        # Initialize socket, AF_INET == IPv4 & SOCK_STREAM == TCP
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Avoid bind() exception: OSError: [Errno 48] Address already in use
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(1)
        
    def connect(self):
        
        while True: 
            try:
                if self.clientsocket is None:
                    self.clientsocket, self.address = self.socket.accept()
                    print(f"[ALGO_SERVER] Connection from {self.address} has been established!")
                    break
            except Exception as error:
                print(f"[ALGO_SERVER] Connection with {self.address} failed: {str(error)}")

                if self.clientsocket is not None:
                    self.clientsocket.close()
                    self.clientsocket = None

            print(f"[ALGO_SERVER] Retrying connection with {self.address}")

    def disconnect_clientsocket(self):
        try:
            if self.clientsocket is not None:
                print(f"[ALGO_SERVER] Disconnecting Client Socket...")
                self.clientsocket.close()
                self.clientsocket = None

        except Exception as error:
            print(f"[ALGO_SERVER] Client Socket disconnect failed: {str(error)}" )

    def disconnect_all(self):
        self.disconnect_clientsocket()
        try:
            if self.socket is not None:
                print(f"[ALGO_SERVER] Disconnecting Server Socket...")
                self.socket.close()
                self.socket = None
            
        except Exception as error:
            print(f"[ALGO_SERVER] Server Socket disconnect failed: {str(error)}")

    def recv(self):
        
        try:
            message = self.clientsocket.recv(ALGO_SOCKET_BUFFER_SIZE).strip()
            
            if len(message) > 0:
                print(f'[ALGO_SERVER] Message from Algo: {message}')
                return message
            return None

        except Exception as error:
            print(f'[ALGO_SERVER] Fails to recv from algo: {str(error)}')
            raise error

    def send(self, message):
        try:
            print(f"[ALGO_SERVER] To Algo: {message}")
            self.clientsocket.send(message)

        except Exception as error:
            print(f'[ALGO_SERVER] Fails to send to algo: {str(error)}')
            raise error

if __name__ == '__main__':
    message = ""
    server = AlgoServer()
    server.connect()
    while True:
        try:
            server.send(message.encode())
            received = server.recv()
        except KeyboardInterrupt:
                print("User has pressed ctrl-c button")
                break