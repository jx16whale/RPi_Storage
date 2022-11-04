from datetime import datetime
import time
import imagezmq
from multiprocessing import Process, Value, SimpleQueue, Queue
from commServers.config import IMAGE_FORMAT, IMAGE_HEIGHT, IMAGE_WIDTH

# Camera modules
from picamera import PiCamera
from picamera.array import PiRGBArray

# Servers
from commServers.stmServer import STMServer
from commServers.androidServer import AndroidServer

class MultiProcessing3:
    def __init__(self, image_processing_server:str, android_on:bool, stm_on: bool):

        print(f"[MAIN] Initialising Multi Process")
        self.stop_sleep = Value('i', 0)
        self.image_processing_avail =  Value('i', 0)
        self.image_count = Value('i', 0)
        self.stop_process = Value('i',0)
        self.stm = None
        self.android = None
        self.image_processing_server = None
        
        # STM
        if stm_on:
            print(f"[MAIN] Initialising STM processes")
            self.stm = STMServer()
            self.stm_message_queue = Queue()
            self.write_stm_process = Process(target=self._write_stm, name = "[STM Write Process]")
            
        # Android
        if android_on:
           print(f"[MAIN] Initialising Android processes") 
           self.android = AndroidServer()
           self.read_android_process = Process(target=self._read_android, name="[Android Read Process]")
            
        # Image Processing
        if image_processing_server is not None:
            print(f"[MAIN] Initialising Image-Processing processes") 
            self.image_queue = SimpleQueue()
            self.image_processing_server = image_processing_server 
            self.take_img = Process(target = self.take_pic, name="[Take Image]")
            #self.image_process = Process(target=self.image_processing, name="[Image Process]")
            
    def start(self):
        try:
            # STM Instance
            if self.android is not None:
                self.android.connect()
                self.read_android_process.start()
            if self.stm is not None:
                self.stm.connect()
                self.write_stm_process.start()
                # self.stm_message_queue.put_nowait(b"w100")
                # self.image_processing_avail.value = 1                            
            # Image Processing
            if self.image_processing_server is not None:
                self.take_img.start()
                #self.image_process.start()
            print('[MAIN] Started all connection')
        except Exception as error:
            print(f"[MAIN] Failed to start connection!")
            raise(error)


        self.image_processing()

        
    def end(self):
    
        if self.android is not None:
            self.read_android_process.terminate()
            self.read_android_process.join()
            self.android.disconnect_all()
        if self.stm is not None:
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
                    time.sleep(1.2)
                    self.image_processing_avail.value = 1
                    break
            
                else:
                    print(f"[MAIN] Android message not recognised: {raw_message}")
                      
            except Exception as error:
                print(f'[MAIN] Android error when reading!')
                raise(error)

           
    def _write_stm(self):
        while True:
            try:
                # Send only if STM is ready to receive.
                if self.stm_message_queue.empty() :
                    continue
                
                message = self.stm_message_queue.get_nowait()
                
                self.stm.send(message)                

                print(f"[MAIN] STM Completed {message}.")
                
                    
            except Exception as error:
                print(f'[MAIN] STM error when writing')
                raise(error)
             
    def take_pic(self):
        camera = PiCamera(resolution=(IMAGE_WIDTH, IMAGE_HEIGHT))
        
        # Warmup camera
        time.sleep(1.5)
        while True:
            try:
                
                if self.image_processing_avail.value == 1:
                    if self.stop_sleep.value == 0 and self.image_count.value == 1:
                        print("TEST")
                       #time.sleep()
                        self.stop_sleep.value= 1
                    # Capture image in BGR format for cv2
                    start_time = datetime.now()
                    rawCapture = PiRGBArray(camera)
                    camera.capture(rawCapture, format=IMAGE_FORMAT)
                    image = rawCapture.array
                    #print(f'[MAIN] Picture taken')
                    print(f'[MAIN] Time taken to take picture: {str(datetime.now() - start_time)} seconds')
                    self.image_queue.put([image, "test"])
                    self.stop_process.value = 0

                    
                elif self.image_count.value == 2:
                    camera.close()
                    #self.end()    

    
            except Exception as error:
                print(f"[MAIN] Failed to Take Picture!")
                raise(error)
        

    def image_processing(self):
        image_sender = imagezmq.ImageSender(connect_to=self.image_processing_server)
        
        while True:
            try:
                if self.image_queue.empty(): continue
 
                image_message = self.image_queue.get()
                    
                print(f"[MAIN] Sending image for processing")
                start = datetime.now()
                reply = image_sender.send_image(image_message[1], image_message[0])
                print(f'[MAIN] Time taken to process image: {str(datetime.now() - start)} seconds')                
                # right arrow
                if reply == b"38":
                    self.image_processing_avail.value = 0 # Stop taking temp
                    self.image_count.value += 1
                    print(self.image_count.value)
                    if self.image_count.value == 1:
                        command = b"d100"
                    else:
                        command = b"d200"
                    self.stm_message_queue.put_nowait(command)

                    # Remove old pics from queue
                    #while not self.image_queue.empty():
                    while self.image_count.value in [1,2]:
                        print("Removed")
                        self.image_queue.get()
                        if self.image_queue.empty():
                            break
                        



                elif reply == b"39":
                    self.image_processing_avail.value = 0
                    self.image_count.value += 1
                    print(self.image_count.value)
                    if self.image_count.value == 1:
                        command = b"a100"
                    else:
                        command = b"a200"
                        #command = b'd200'
                        
                    self.stm_message_queue.put_nowait(command)
                    
                   # # Remove old pics from queue
                    #while not self.image_queue.empty():
                     #   print("Removed")
                      #  self.image_queue.get()
                    while self.image_count.value in [1,2]:
                        print("Removed")
                        self.image_queue.get()
                        if self.image_queue.empty():
                            break
                

              
                if self.image_queue.empty():
                    print("test")
                    self.image_processing_avail.value = 1
                                   
            except Exception as error:
                print(f'[MAIN] Error Image processing!')
                raise(error)
            
        