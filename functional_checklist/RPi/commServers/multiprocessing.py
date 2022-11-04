

from datetime import datetime
import time
import imagezmq
from multiprocessing import Process, Value, Queue, Manager
from commServers.config import IMAGE_FORMAT, IMAGE_HEIGHT, IMAGE_WIDTH

# Camera modules
from picamera import PiCamera
from picamera.array import PiRGBArray


# Servers
from commServers.stmServer import STMServer
from commServers.algoServer import AlgoServer
from commServers.androidServer import AndroidServer

class MultiProcessing:
    def __init__(self, image_processing_server:str, android_on: bool, stm_on: bool, algo_on: bool):
        
        print(f"[MAIN] Initialising Multi Process")
        self.image_count = Value('i',6)
        self.stm_ready_recv = Value('i', 1)
        self.image_processing_avail = Value('i', 1)
        self.stm = self.android = self.algo = self.image_process = None
        self.image_processing_server = self.stm_on = self.android_on = self.algo_on = False
        #self.manager = Manager()
        #self.manager.start()
        # STM
        if stm_on:
            print(f"[MAIN] Initialising STM processes")
            self.stm_on = True
            self.stm = STMServer()
            self.stm_message_queue = Queue()
            self.read_stm_process = Process(target=self._read_stm, name="[STM Read Process]")
            self.write_stm_process = Process(target=self._write_stm, name = "[STM Write Process]")
        
        # Android
        #if android_on:
           # print(f"[MAIN] Initialising Android processes") 
           # self.android_on = True
           # self.android = AndroidServer()
           # self.android_message_queue = Queue()
           # self.read_android_process = Process(target=self._read_android, name="[Android Read Process]")
           # self.write_android_process = Process(target=self._write_android, name="[Android Write Process]")

        # algo
        if algo_on: 
            print(f"[MAIN] Initialising Algo processes") 
            self.algo_on = True
            self.algo = AlgoServer()
            self.algo_message_queue = Queue()
            self.read_algo_process = Process(target=self._read_algo, name="[Algo Read Process]")
            self.write_algo_process = Process(target=self._write_algo, name="[Algo Write Process]")

        # Image Processing
        if image_processing_server is not None:
            print(f"[MAIN] Initialising Image-Processing processes") 
            self.image_queue = Queue()
            self.image_processing_server = image_processing_server 
            self.image_process = Process(target=self.image_processing, name="[Image Process]")
            
            
    def start(self):
        try:
            # STM Connection
            if self.stm is not None:
                self.stm.connect()
                self.write_stm_process.start()
                self.read_stm_process.start()
            
            # Android Connection
            if self.android is not None:
                self.android.connect()
                self.write_android_process.start()
                self.read_android_process.start()
                
            # algo Connection

            if self.algo is not None:
                self.algo.connect()
                self.write_algo_process.start()
                self.read_algo_process.start()
                self.algo.send(b"start\n")

            # Image Processing
            if self.image_processing_server is not None:
                self.image_process.start()

            print('[MAIN] Started all connection')

        except Exception as error:
            print(f"[MAIN] Failed to start connection: {error}")
            
        # Continously check if reconnection is needed.
        #self.allow_reconnection()
        
    def end(self):
        if self.stm is not None: self.stm.disconnect()
        if self.android is not None: self.android.disconnect_all()
        if self.algo is not None: self.algo.disconnect_all()
        print("[MAIN] Multi Process has ended.")
        
    def _allow_reconnection(self):
        print(f'[MAIN] RPi can reconnect now')

        while True:
            try:
                if self.algo_on and (not self.read_algo_process.is_alive() or not self.write_algo_process.is_alive()):
                    self._reconnect_algo()

                if self.stm_on and (not self.read_stm_process.is_alive() or not self.write_stm_process.is_alive()):
                    self._reconnect_stm()
                    
                if self.android_on and (not self.read_android_process.is_alive() or not self.write_android_process.is_alive()):
                    self._reconnect_android()                 
                
                if self.image_process is not None and not self.image_process.is_alive():
                   self.image_process.terminate()
                   self.image_process = Process(target=self.image_processing, name="[Image Process]")
                   self.image_process.start()
                    
            except Exception as error:
                print(f"[MAIN] Error during reconnection: {error}")
                
    def _reconnect_android(self):
        self.android.disconnect()
        
        self.read_android_process.terminate()
        self.write_android_process.terminate()
        
        self.android.connect()
        
        self.read_android_process = Process(target=self._read_android)
        self.read_android_process.start()
        
        self.write_android_process = Process(target=self._write_android)
        self.write_android_process.start()

        print(f'[MAIN] Successfully reconnected to Android')
        
    def _reconnect_algo(self):
        self.algo.disconnect()

        self.read_algo_process.terminate()
        self.write_android_process.terminate()

        self.algo.connect()

        self.read_algo_process = Process(target=self._read_algo)
        self.read_algo_process.start()

        self.write_algo_process = Process(target=self._write_algo)
        self.write_algo_process.start()

        print(f'[MAIN] Successfully reconnected to algo')
        
    def _reconnect_stm(self):
        self.stm.disconnect()
        
        self.read_stm_process.terminate()
        self.write_stm_process.terminate()

        self.stm.connect()

        self.read_stm_process = Process(target=self._read_stm)
        self.read_stm_process.start()

        self.write_stm_process = Process(target=self._write_stm)
        self.write_stm_process.start()

        print(f'[MAIN] Successfully reconnected to stm')
    
    def _read_algo(self):
        while True:
            try:
                raw_message = self.algo.recv()
                
                if raw_message is None: continue
                
                # Split raw_message into list of commands
                if "|" in raw_message:
                    message = raw_message.split('|')
                
                    if message[0] == "MOVE":
                        if self.stm is None:
                            print(f"[MAIN] STM connection is down.")
                            continue
                    
                    # Send Movement to STM
                        else:
                            for movement in message[1:-1]:
                                self.stm_message_queue.put_nowait(movement.encode())
                            self.obstacle_id = message[-1][1]
                            
                    elif message[0] == "M":
                        if self.stm is None:
                            print(f"[MAIN] STM connection is down.")
                            continue
                        else:
                            for movement in message[1:]:
                                self.stm_message_queue.put_nowait(movement.encode())
                            #self.obstacle_id = message[-1][1]
                
                    else:
                        print(f"[MAIN] Algo To STM Command Type not recognised: {message}")
                        break
                else:
                    if raw_message[0] == "s":
                        image = self.take_pic()
                        print(f'[MAIN] Picture taken')
                        self.image_queue.put_nowait([image, f"{self.image_count.value}"])
                        continue
                        
                    if raw_message[0] == "R":
                        if self.android is None:
                            print(f"[MAIN] Android connection is down")
                            continue
                            
                         # Update Robot Position on APP  
                        else:
                            self.android_message_queue.put_nowait(message.encode())
                
                    else:
                        print("[MAIN] Algo to Android Command Type not recognised: {message}")            

            except Exception as error:
                print(f"[MAIN] Error Reading Algo Process : {error}")                 
                
    def _write_algo(self):
        while True:
            try:
                if not self.algo_message_queue.empty():
                    message = self.algo_message_queue.get_nowait()
                    self.algo.send(message)
                    
            except Exception as error:
                print(f'[MAIN] Error writing to algo: {error}')
                break
            
    def _read_android(self):
        while True:
            try:
                raw_message = self.android.recv()
                
                if raw_message is None: 
                    continue
                
                if len(raw_message) > 4:
                # Coord messsage to algo, e.g. OBS__1,2,3,4\nOBS__2,3,6,4\nOBS__3,5,18,2\nOBS...\nDRAW_PATH\nBANANAS\n
                    if raw_message[0] == 'O':
                        if self.algo is None:
                            print(f"[MAIN] Algo connection is down")
                            continue
                        
                        else:
                            self.algo_message_queue.put_nowait(f"{raw_message}\nDRAW_PATH\nBANANAS\n".encode())
                        
                    else:
                        print("[MAIN] Android to Algo Command Type not recognised: {message}")
                    
                # Manual control by android tablet, e.g. w010, a000, s010, d000
                else:
                    if raw_message[0] in ['w','a','s','d']:
                        if self.stm is None:
                            print(f"[MAIN] STM connection is down.")
                            continue
                        else:
                            #print("test")
                            self.stm_message_queue.put_nowait(raw_message.encode())
                            #print("works")
                            self.image_processing_avail.value = 0
                            # self.stm.send(raw_message)
                            # self.stm_ready_recv.value = 0
                    
                            # while self.stm_ready_recv.value != 1:
                            #     continue
                    
                            # print(f"[MAIN] STM Completed {raw_message}.")
                    
                    else:
                       print("[MAIN] Android to STM Command Type not recognised: {message}") 
            
            except Exception as error:
                print(f"[MAIN] Error Reading Android Process : {error}")
                break
                       
    def _write_android(self):
        while True:
            try:
                if not self.android_message_queue.empty():
                    message = self.android_message_queue.get_nowait()
                    self.android.send(message)
            except Exception as error:
                print(f'[MAIN] Error Writing Android Process: {error} ')
                break
            
    def _read_stm(self):
        while True:
            try:
                raw_message = self.stm.recv()
                
                if raw_message is None:
                    continue
                
                elif raw_message == b'A':
                    self.stm_ready_recv.value = 1
                    print(f"[MAIN] STM ready to read next instruction")
                
                else:
                    print(f"[MAIN] STM message not recognised:  {raw_message}")
                    
            except Exception as error:
                print(f'[MAIN] STM error when reading: {error}')
                break   
    
    def _write_stm(self):
        while True:
            try:
                # Send only if STM is ready to receive.
                if self.stm_message_queue.empty() or self.stm_ready_recv.value != 1:
                    continue
                
                message = self.stm_message_queue.get_nowait()
                
                self.stm.send(message)
                self.stm_ready_recv.value = 0
                
                while self.stm_ready_recv.value != 1:
                    continue
                
                print(f"[MAIN] STM Completed {message}.")
                
                # Finish all movements to obstacle, can take picture of obstacle now
                if self.stm_message_queue.empty() and self.image_processing_avail.value == 1: #and  self.stm_ready_recv.value == 1:
                    image = self.take_pic()
                    print(f'[MAIN] Picture taken')
                    self.image_queue.put_nowait([image, f"{self.image_count.value}"])
                    
                    
            except Exception as error:
                print(f'[MAIN] STM error when writing: {error}')
                break
            
    def take_pic(self):
        try:
            start_time = datetime.now()
            camera = PiCamera(resolution=(IMAGE_WIDTH, IMAGE_HEIGHT))
            rawCapture = PiRGBArray(camera)
            
            # Warmup camera
            time.sleep(1.5)
            
            # Capture image in BGR format for cv2
            camera.capture(rawCapture, format=IMAGE_FORMAT)
            image = rawCapture.array
            camera.close()
            print(f'[MAIN] Time taken to take picture: {str(datetime.now() - start_time)} seconds')
        except Exception as error:
            print(f"[MAIN] Failed to Take Picture: {error}")
        
        return image
    
    def image_processing(self):
        image_sender = imagezmq.ImageSender(connect_to=self.image_processing_server)
        
        while True:
            try:
                if self.image_queue.empty(): continue
                
                # 3 Tries Max
                # self.image_processing_avail.value = 0
                reverse = 0
                image_message = self.image_queue.get_nowait()
                start_time = datetime.now()
                #for attempt in range(1,3):
                #print(f"[MAIN] Attmept to send image for processing : No.{attempt + 1}")
                reply = image_sender.send_image(image_message[1], image_message[0]).decode()
                    
                
                    #if reply in [b'-1', b'16']:
                        # Move backwards
                       # print('[MAIN] Failed to detect image, re-attmepting...')
                        #self.stm_ready_recv.value = 0
                        #self.stm.send(b's010')
                        
                        #while self.stm_ready_recv.value != 1:
                        #    continue
                        
                        #reverse = attempt
                        #image = self.take_pic()
                        #image_message = [image, f"{self.image_count.value}"]
                        
                    #else:
                image_id = f"{reply}\n"
                print(f'[MAIN] Time taken to process image: {str(datetime.now() - start_time)} seconds')
                # Update android for Image Target ID on Obstacle Blocks
                #self.android_message_queue.put_nowait(f"TARGET,{self.obstacle_id},{image_id}".encode())
                self.algo_message_queue.put_nowait(image_id.encode())
                        #break
                        # self.image_count.value -= 1
                        
                        # # Finished image rec
                        # if self.image_count.value == 0:
                        #     break

                        # while reverse != 0:
                        #     self.stm_message_queue.put_nowait(b'w010')
                        #     reverse -= 1
                                
                        # while self.stm_ready_recv.value != 1:
                        #     continue
                        
                        # self.image_processing_avail.value = 1
                        
                        # self.algo_message_queue.put_nowait(f"DONE\n".encode())
                        # break
                self.image_count.value -= 1
                
                # No more images to detect
                if self.image_count.value == 0:
                    break
                
                 # Reverse back to original position
                if reverse != 0 and self.image_count.value != 0:
                    
                    while reverse != 0:
                        self.stm_ready_recv.value = 0
                        self.stm.send(b'w010')
                        # self.stm_message_queue.put_nowait(b'w010')
                        reverse -= 1
                        while self.stm_ready_recv.value != 1:
                            continue
           
                    # self.image_processing_avail.value = 1
                    # self.algo_message_queue.put_nowait(f"DONE\n".encode())
                    self.algo.send(b"DONE\n")
                        
            except Exception as error:
                print(f'[MAIN] Error Image processing: {error}')
