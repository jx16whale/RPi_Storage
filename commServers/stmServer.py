from commServers.config import BAUD_RATE, SERIAL_PORT
import serial
import time 

class STMServer:
    def __init__(self, serial_port=SERIAL_PORT, baud_rate=BAUD_RATE):
        self.flip = 0
        self.serial_port = serial_port[self.flip]
        self.baud_rate = baud_rate
        self.connection = None

    def connect(self):
        
        while True:

            try:
                print(f'[STM_SERVER] Establishing connection with STM')

                self.connection = serial.Serial(self.serial_port, self.baud_rate)

                if self.connection is not None:
                    print(f"[STM_SERVER] Connection from {str(self.connection.name)} has been established!")
                    break

            except Exception as error:
                    print(f"[STM_SERVER] Connection with STM failed: {str(error)}")
                    if error.errno == 2:
                        self.flip ^= 1
                        self.serial_port = SERIAL_PORT[self.flip]
                    time.sleep(1)
                    
            print(f'[STM_SERVER] Retrying STM connection...')


    def disconnect(self):
        try:
            if self.connection is not None:
                print(f"[STM_SERVER] Disconnecting connection...")
                self.connection.close()
                self.connection = None

        
        except Exception as error:
            print(f'[STM_SERVER] STM disconnect failed: {str(error)}')
            
    def recv(self):
        try:
            message = self.connection.read(1).strip()
            print(f'[STM_SERVER] Message From STM: {message}')

            if len(message) > 0:
                return message

            return None
       
        except Exception as error:
            print(f'[STM_SERVER] Fails to recv from STM: {str(error)}')
            raise error
    
    def send(self, message):
        try:
            print(f'[STM_SERVER] Message To STM: {message}')
            self.connection.write(message)

        except Exception as error:
            print(f'[STM_SERVER] Fails to send to STM: {str(error)}')
            raise error
        
if __name__ == '__main__':
    message = b"w100"
    server = STMServer()
    server.connect()
    test = True
    while test:
        try:
            server.send(message)
            time.sleep(1)
            received = server.recv()
            if received == b"A":
                test = False
        except:
            print("User has pressed ctrl-c button")
        


    