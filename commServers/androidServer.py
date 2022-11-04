import bluetooth as bt
import os
from commServers.config import ANDROID_SOCKET_BUFFER_SIZE, RFCOMM_CHANNEL, UUID

class AndroidServer:
    def __init__(self):
        
        self.server_sock = None
        self.clientsocket = None
        os.system("sudo hciconfig hci0 piscan")
        self.server_sock = bt.BluetoothSocket(bt.RFCOMM)
        self.server_sock.bind(("", 1))

        self.server_sock.listen(1)
        bt.advertise_service(
            self.server_sock,
            'MDP_Group15_RPi',
            profiles=[bt.SERIAL_PORT_PROFILE],
            service_id = UUID,
            service_classes = [UUID, bt.SERIAL_PORT_CLASS]
        )

        print(f'[AND_SERVER] server socket: {str(self.server_sock)}')

    def connect(self):
        while True:
            try:
                if self.clientsocket is None:
                    self.clientsocket, address = self.server_sock.accept()
                    print(f"[AND_SERVER] Connection from {str(address)} has been established!")
                    break
            except Exception as error:
                print(f"[AND_SERVER] Connection with android failed: {str(error)}")

                if self.clientsocket is not None:
                    self.clientsocket.close()
                    self.clientsocket = None
                    
            print(f'[AND_SERVER] Retrying connection with android...')

    def disconnect_clientsocket(self):
        try:
            if self.clientsocket is not None:
                print(f"[AND_SERVER] Disconnecting Client Socket...")
                self.clientsocket.close()
                self.clientsocket = None


        except Exception as error:
            print(f"[AND_SERVER] Client Socket disconnect failed: {str(error)}")

    def disconnect_all(self):
        # try:
        #     if self.clientsocket is not None:
        #         self.clientsocket.close()
        #         self.clientsocket = None 
        self.disconnect_clientsocket()
        
        try:
            if self.server_sock is not None:
                print(f"[AND_SERVER] Disconnecting Server Socket...")
                self.server_sock.close()
                self.server_sock = None

        except Exception as error:
            print(f"[AND_SERVER] Server Socket disconnect failed: {str(error)}")

    def recv(self):
        try:
            message = self.clientsocket.recv(ANDROID_SOCKET_BUFFER_SIZE).strip().decode()

            # if message is None:
            #     return None

            if len(message) > 0:
                print(f'[AND_SERVER] Message from android: {message}')
                return message

            return None

        except Exception as error:
            print(f'[AND_SERVER] Fails to recv from android: {str(error)}')
            raise error

    def send(self, message):
        try:
            print(f'[AND_SERVER] To Android: {message}')
            self.clientsocket.send(message)

        except Exception as error:
            print(f'[AND_SERVER] Fails to send to android: {str(error)}')
            raise error

if __name__ == '__main__':
    A = AndroidServer()
    A.connect()
    try:
        while True:
            A.recv()
            A.send(input(f"[Android] Send Message: "))
    except KeyboardInterrupt:
        print("[Android] Terminating the program now...")    