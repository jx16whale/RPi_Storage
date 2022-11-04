import os
from bluetooth import *
from config import ANDROID_SOCKET_BUFFER_SIZE, UUID

class Android:
    def __init__(self) -> None:
        print("[Android] Initialising Android Process")
        self.server_socket = None
        self.client_socket = None
        os.system("sudo hciconfig hci0 piscan")
        self.server_socket = BluetoothSocket(RFCOMM)
        self.server_socket.bind(("", PORT_ANY))
        self.server_socket.listen(1)
        self.port = self.server_socket.getsockname()[1]
        advertise_service(
            self.server_socket, 
            'MDP_Group_12',
            service_id=UUID,
            service_classes=[UUID, SERIAL_PORT_CLASS],
            profiles=[SERIAL_PORT_PROFILE],
            #protocols = [ OBEX_UUID ]
        )
        print(f'[Android] Server Bluetooth Socket: {str(self.server_socket)}')
    
    def connect(self) -> None:
        retry = True
        while retry:
            try:
                print(f"[Android] Listening on RFCOMM channel: {self.port}...")
                if self.client_socket == None:
                    self.client_socket, client_addr = self.server_socket.accept()
                    print(f"[Android] Bluetooth established connection at address: {str(client_addr)}")
                    retry = False
            except Exception as error:
                print(f"[Android] Failed to establish Bluetooth Connection: {str(error)}")
                self.disconnect_client()
                retry = True
                print(f"[Android] Retrying Bluetooth Connection...")

    def disconnect_client(self) -> None:
        try:
            if self.client_socket != None:
                self.client_socket.close()
                self.client_socket = None
        except Exception as error:	
            print(f"[Android] Fail to disconnect Client Socket: {str(error)}")

    def disconnect_server(self) -> None:
        try:
            if self.server_socket != None:
                self.server_socket.close()
                self.server_socket = None
        except Exception as error:	
            print(f"[Android] Fail to disconnect Server Socket: {str(error)}")

    def disconnect_all(self) -> None:
        self.disconnect_client()
        self.disconnect_server()

    # Receive from Android Interface
    def recv(self) -> None:
        try:
            message = self.client_socket.recv(ANDROID_SOCKET_BUFFER_SIZE).strip()
            if message is None:
                return None
            if len(message) > 0:
                return message
            return None
        except Exception as error:
            print(f"[Android] Fail to recieve message from Android {str(error)}")
            raise error
    
    # Send To Android Interface
    def send(self, message) -> None:
        try:
            print(f'[Android] Message to Android: {message}')
            self.client_socket.send(message)
        except Exception as error:	
            print(f"[Android] Fail to send {str(error)}")
            raise error

# Standalone testing.
if __name__ == '__main__':
    android = Android()
    android.connect()
    try:
        while True:
            android.recv()
            android.send(input(f"[Android] Send Message: "))
    except KeyboardInterrupt:
        print("[Android] Terminating the program now...")   