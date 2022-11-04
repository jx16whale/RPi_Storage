from datetime import datetime
import time
import imagezmq
from multiprocessing import Process, Value, Queue
from commServers.config import IMAGE_FORMAT, IMAGE_HEIGHT, IMAGE_WIDTH

# Camera modules
from picamera import PiCamera
from picamera.array import PiRGBArray

# Servers
from commServers.stmServer import STMServer
from commServers.androidServer import AndroidServer

class MultiProcessing2:
    def __init__(self, image_processing_server:str, android_on:bool, stm_on: bool):
        print(f"[MAIN] Initialising Multi Process")
        self.stm_ready_recv = Value('i', 0)
        self.image_processing_avail =  Value('i', 0)
        self.image_count = Value('i', 0)
        self.first = Value('i',0)
        self.stm =  None
        self.android = None
        self.image_process_server = None

        # Android
      
        # STM
        if stm_on:
            print(f"[MAIN] Initialising STM processes")
            self.stm = STMServer()
            self.stm_message_queue = Queue()
            self.read_stm_process = Process(target=self._read_stm, name="[STM Read Process]")
            self.write_stm_process = Process(target=self._write_stm, name = "[STM Write Process]")
            

            
        # Image Processing
        if image_processing_server is not None:
            print(f"[MAIN] Initialising Image-Processing processes") 
            self.image_queue = Queue()
            self.image_processing_server = image_processing_server 
            self.image_process = Process(target=self.image_processing, name="[Image Process]")
            
        if android_on:
           print(f"[MAIN] Initialising Android processes") 
           self.android = AndroidServer()
           self.read_android_process = Process(target=self._read_android, name="[Android Read Process]") 
            
    def start(self):
        try:
            # STM Instance
            if self.stm is not None:
                self.stm.connect()
                self.write_stm_process.start()
                self.read_stm_process.start()

            if self.android is not None:
                self.android.connect()
                self.read_android_process.start()
                
                           
            # Image Processing
            if self.image_processing_server is not None:
                self.image_process.start()
            print('[MAIN] Started all connection')
        except Exception as error:
            print(f"[MAIN] Failed to start connection!")
            raise(error)
        # self.stm_message_queue.put_nowait(b"w100")

        self.take_pic()
        
    def end(self):
        if self.stm is not None:
            self.read_stm_process.terminate()
            self.read_stm_process.join()
            self.write_stm_process.terminate()
            self.write_stm_process.join()
            self.stm_message_queue.close()
            self.stm.disconnect()
            
        if self.image_processing_server is not None:
            self.image_process.terminate()
            self.image_process.join()
            self.image_queue.close()
            
        print("[MAIN] Multi Processing has ended.")

    def _read_android(self):
        while True:
            try:
                raw_message = self.android.recv()
                if raw_message is None: continue
                
                elif raw_message == 'Fastest':
                    self.stm_message_queue.put_nowait(b"w100")
                    break
            
                else:
                    print(f"[MAIN] Android message not recognised: {raw_message}")
                      
            except Exception as error:
                print(f'[MAIN] Android error when reading!')
                raise(error)
            
                    
    
    def _read_stm(self):
        while True:
            try:

                raw_message = self.stm.recv()
                
                if raw_message is None:
                    continue
                
                # confirmation reply to recv next command
                elif raw_message == b'A':
                    #self.first.value += 1
                    self.stm_ready_recv.value = 1
                    # print(f"[MAIN] STM ready to read next instruction")
                    #if not self.first.value == 1:
                    if self.image_count.value <= 1:
                        self.image_processing_avail.value = 1
                        print(f"[MAIN] RPi Taking Picture")
                    while self.stm_ready_recv.value == 1:
                        continue

                else:
                    print(f"[MAIN] STM message not recognised: {raw_message}")
                    
            except Exception as error:
                print(f'[MAIN] STM error when reading!')
                raise(error)
            
            
    def _write_stm(self):
        while True:
            try:
                # Send only if STM is ready to receive.
                if self.stm_message_queue.empty():
                    continue
                
                message = self.stm_message_queue.get_nowait()
                time.sleep(0.1)
                self.stm.send(message)
                #time.sleep(1)
                self.stm_ready_recv.value = 0
                

                print(f"[MAIN] STM Completed {message}.")
                
                    
            except Exception as error:
                print(f'[MAIN] STM error when writing')
                raise(error)
             
    def take_pic(self):
        try:
            camera = PiCamera(resolution=(IMAGE_WIDTH, IMAGE_HEIGHT))
            
            # Warmup camera
            time.sleep(1.5)
            while True:
                if self.image_processing_avail.value == 1:
                    # Capture image in BGR format for cv2
                    start_time = datetime.now()
                    rawCapture = PiRGBArray(camera)

                    camera.capture(rawCapture, format=IMAGE_FORMAT)
                    image = rawCapture.array
                    #print(f'[MAIN] Picture taken')
                    print(f'[MAIN] Time taken to take picture: {str(datetime.now() - start_time)} seconds')
                    self.image_queue.put_nowait([image, "test"])
                    self.image_processing_avail.value = 0
                    
                #elif self.image_count.value == 2:
                    #camera.close()
                    #self.end()
    
        except Exception as error:
            print(f"[MAIN] Failed to Take Picture!")
            raise(error)
        

    def image_processing(self):
        image_sender = imagezmq.ImageSender(connect_to=self.image_processing_server)
        
        while True:
            try:
                if self.image_queue.empty(): continue
                
                image_message = self.image_queue.get_nowait()
                print(f"[MAIN] Sending image for processing")
                start = datetime.now()
                reply = image_sender.send_image(image_message[1], image_message[0])
                print(f'[MAIN] Time taken to process image: {str(datetime.now() - start)} seconds')                
                # right arrow
                if reply == b"38":
                    if self.image_count.value == 0:
                        command = b"d100"
                    else:
                        command = b"d200"
                    self.stm_message_queue.put_nowait(command)
                # left arrow
                elif reply == b"39":
                    if self.image_count.value == 0:
                        command = b"a100"
                    else:
                        command = b"a200"
                    self.stm_message_queue.put_nowait(command)
                else:
                    continue
                self.image_count.value += 1
                                   
            except Exception as error:
                print(f'[MAIN] Error Image processing!')
                raise(error)
            
        