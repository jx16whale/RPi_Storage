from datetime import datetime
import time
import imagezmq
from multiprocessing import Process, Value, Queue
from commServers.config import IMAGE_FORMAT, IMAGE_HEIGHT, IMAGE_WIDTH
from ctypes import c_wchar_p, c_wchar

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
        
        # Intialise all the shared variables
        self.image_count = Value('i',8)
        self.stm_ready_recv = Value('i', 1)
        self.image_processing_avail = Value('i', 0)
        self.obstacle_id = Value(c_wchar, '1')
        self.x_coord = Value('i', 1)
        self.y_coord = Value('i', 1)
        self.direction = Value(c_wchar, '1')

        self.stm = None
        self.android = None
        self.algo = None
        self.image_processing_server =None

        # STM
        if stm_on:
            print(f"[MAIN] Initialising STM processes")
            self.stm = STMServer()
            self.stm_message_queue = Queue()
            self.read_stm_process = Process(target=self._read_stm, name="[STM Read Process]")
            self.write_stm_process = Process(target=self._write_stm, name = "[STM Write Process]")
        
        # algo
        if algo_on: 
            print(f"[MAIN] Initialising Algo processes") 
            self.algo = AlgoServer()
            self.algo_message_queue = Queue()
            self.read_algo_process = Process(target=self._read_algo, name="[Algo Read Process]")
            self.write_algo_process = Process(target=self._write_algo, name="[Algo Write Process]")
        
        # Android
        if android_on:
           print(f"[MAIN] Initialising Android processes") 
           self.android = AndroidServer()
           self.android_message_queue = Queue()
           self.read_android_process = Process(target=self._read_android, name="[Android Read Process]")
           self.write_android_process = Process(target=self._write_android, name="[Android Write Process]")

        # Image Processing
        if image_processing_server is not None:
            print(f"[MAIN] Initialising Image-Processing processes") 
            self.image_processing_avail.value = 1
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
                
            # algo Connection
            if self.algo is not None:
                self.algo.connect()
                self.write_algo_process.start()
                self.read_algo_process.start()
            
            # Android Connection
            if self.android is not None:
                self.android.connect()
                self.write_android_process.start()
                self.read_android_process.start()

            # Image Processing
            if self.image_processing_server is not None:
                self.image_process.start()

            print('[MAIN] Started all connection')


        except Exception as error:
            print(f"[MAIN] Failed to start connection!")
            raise(error)

        # Stop main process from ending prematurely (if use Manager)
        #self._wait_processes_done()
        
    def end(self):
        
        if self.stm is not None:
            self.read_stm_process.terminate()
            # self.read_stm_process.join()
            self.write_stm_process.terminate()
            # self.write_stm_process.join()
            self.stm_message_queue.close()
            self.stm.disconnect()
            
        if self.android is not None: 
            self.read_android_process.terminate()
            # self.read_android_process.join()
            self.write_android_process.terminate()
            # self.write_android_process.join()
            self.android_message_queue.close()
            self.android.disconnect_all()
            
        if self.algo is not None: 
            self.read_algo_process.terminate()
            # self.read_algo_process.join()
            self.write_algo_process.terminate()
            # self.write_algo_process.join()
            self.algo_message_queue.close()
            self.algo.disconnect_all()
            
        if self.image_processing_server is not None:
            self.image_process.terminate()
            # self.image_process.join()
            self.image_queue.close()
        
        # self.manger.close()
            
        print("[MAIN] Multi Processing has ended.")
         
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
                                if movement in ['s000','w000']:
                                    continue
                                else:
                                    #[self.stm_message_queue.put_nowait(movement.encode()) for movement in message[1:-1]]
                                    self.stm_message_queue.put_nowait(movement.encode())
                                    self.obstacle_id.value = message[-1][1]
                                    # self.coord['obstacle_id']= message[-1][1]
                            
                    elif message[0] == "M":
                        if self.stm is None:
                            print(f"[MAIN] STM connection is down.")
                            continue
                        else:
                            [self.stm_message_queue.put_nowait(movement.encode()) for movement in message[1:]]

                
                    else:
                        print(f"[MAIN] Algo To STM Command Type not recognised: {message}")
                        break
                else:
                    # if raw_message[0] == "s":
                    #     image = self.take_pic()
                    #     print(f'[MAIN] Picture taken')
                    #     self.image_queue.put_nowait([image, f"{self.image_count.value}"])
                    #     continue
                        # ROBOT,<x>,<y>,<N>
                    if raw_message[0] == "R":
                        if self.android is None:
                            print(f"[MAIN] Android connection is down")
                            continue
                            
                         # Update Robot Position on APP 
                        else:
                            self.android_message_queue.put_nowait(raw_message.encode())
                            message = raw_message.split(",")
                            if message[1][2] == '>':
                                self.x_coord.value = int(message[1][1])
                            else:
                                self.x_coord.value = int(message[1][1:3])

                            if message[2][2] == '>':
                                self.y_coord.value = int(message[2][1])
                            else:
                                self.y_coord.value = int(message[2][1:3])
                            self.direction.value = message[3][1]

                    elif raw_message == "DONE":
                        continue
                    
                    else:
                        print(f"[MAIN] Algo to Android Command Type not recognised: {raw_message}")            

            except Exception as error:
                print(f"[MAIN] Error Reading Algo Process!")
                raise(error)                 
                
    def _write_algo(self):
        while True:
            try:
                if not self.algo_message_queue.empty():
                    message = self.algo_message_queue.get_nowait()
                    self.algo.send(message)
                    self.image_processing_avail.value = 1           # Reset the availability of image processing
                    
            except Exception as error:
                print(f'[MAIN] Error writing to algo!')
                raise(error)
            
    def _read_android(self):
        while True:
            try:
                raw_message = self.android.recv()
                
                if raw_message is None: 
                    continue
                
                if len(raw_message) > 5:

                # Coord messsage to algo, e.g. OBS__1,2,3,4 \nOBS__2,3,6,4 \nOBS__3,5,18,2 \nOBS... \nDRAW_PATH\nBANANAS\n
                    if raw_message[0] == 'O':
                        message = raw_message.split(" \n")
                        self.image_count.value = len(message)
                        if self.algo is None:
                            print(f"[MAIN] Algo connection is down")
                            continue
                        
                        else:
                            self.algo_message_queue.put_nowait(f"{raw_message} \nDRAW_PATH\n".encode())
                    elif raw_message[0] == 'B':
                            self.algo_message_queue.put_nowait(f"{raw_message}\n".encode())
                        
                    else:
                        print("[MAIN] Android to Algo Command Type not recognised: {message}")
                    
                # Manual control by android tablet, e.g. w010, a000, s010, d000
                else:
                    if raw_message[0] in ['w','a','s','d']:
                        if self.stm is None:
                            print(f"[MAIN] STM connection is down.")
                            continue
                        else:
                            self.stm_message_queue.put_nowait(raw_message.encode())
                            self.image_processing_avail.value = 0
                    
                    else:
                       print("[MAIN] Android to STM Command Type not recognised: {message}") 
            
            except Exception as error:
                print(f"[MAIN] Error Reading Android Process!")
                raise(error)
                       
    def _write_android(self):
        while True:
            try:
                if not self.android_message_queue.empty():
                    message = self.android_message_queue.get_nowait()
                    if message[0] == 'T':
                        self.android.send(message.encode())
                    else:
                        time.sleep(1.85)
                        self.android.send(message)
                    if message == b"END":
                        self.end();
            except Exception as error:
                print(f'[MAIN] Error Writing Android Process!')
                raise(error)
            
    def _read_stm(self):
        while True:
            try:
                raw_message = self.stm.recv()
                
                if raw_message is None:
                    continue
                
                # confirmation reply to recv next command
                elif raw_message == b'A':
                    self.stm_ready_recv.value = 1
                    print(f"[MAIN] STM ready to read next instruction")
                
                else:
                    print(f"[MAIN] STM message not recognised: {raw_message}")
                    
            except Exception as error:
                print(f'[MAIN] STM error when reading!')
                raise(error)   
    
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
                
                if self.image_processing_server is None:
                    if self.stm_message_queue.empty():
                        self.algo_message_queue.put_nowait(f"DONE\n".encode())
                
                # Finish all movements to obstacle, can take picture of obstacle now
                elif self.image_processing_server is not None and self.stm_message_queue.empty() and self.image_processing_avail.value == 1:
                    image = self.take_pic()
                    print(f'[MAIN] Picture taken')
                    self.image_queue.put_nowait([image, f"{self.image_count.value}"])
                    
            except Exception as error:
                print(f'[MAIN] STM error when writing')
                raise(error)
            
    def take_pic(self):
        try:
            # start_time = datetime.now()
            camera = PiCamera(resolution=(IMAGE_WIDTH, IMAGE_HEIGHT))
            # camera.rotation = 180
            rawCapture = PiRGBArray(camera)
            
            # Warmup camera
            time.sleep(1.5)
            
            # Capture image in BGR format for cv2
            camera.capture(rawCapture, format=IMAGE_FORMAT)
            image = rawCapture.array
            camera.close()
            # print(f'[MAIN] Time taken to take picture: {str(datetime.now() - start_time)} seconds')
        except Exception as error:
            print(f"[MAIN] Failed to Take Picture!")
            raise(error)
        
        return image
    
    def image_processing(self):
        image_sender = imagezmq.ImageSender(connect_to=self.image_processing_server)
        
        while True:
            try:
                if self.image_queue.empty(): continue
                
                # 3 Tries Max
                reverse = 0
                x_count = 0
                y_count = 0
                image_message = self.image_queue.get_nowait()
                # start_time = datetime.now()
                
                for attempt in range(1,4):
                    print(f"[MAIN] Attmept to send image for processing : No.{attempt}")
                    reply = image_sender.send_image(image_message[1], image_message[0]).decode()
                    print(f"[MAIN] Message from image server: IMAGE_ID = {reply}")

                    # Retry if failed to detect image
                    if reply in ['-1','41'] and attempt != 3:
                        
                        # Move backwards and update android tablet
                        self.image_processing_avail.value = 0   # Prevent _write_stm function from taking pic too
                        print(f'[MAIN] Failed to detect image, re-attmepting...')

                        if self.direction.value == 'N':
                            self.y_coord.value = self.y_coord.value - 1
                        elif self.direction.value == 'S':
                            self.y_coord.value = self.y_coord.value + 1 
                        elif self.direction.value == 'W':
                            self.x_coord.value = self.x_coord.value + 1 
                        else:
                            self.x_coord.value = self.x_coord.value - 1

                        self.stm_ready_recv.value = 0
                        self.stm_message_queue.put_nowait(b's010')
                        self.android_message_queue.put_nowait(f"ROBOT,<{self.x_coord.value}>,<{self.y_coord.value}>,<{self.direction.value}>".encode())
                        # self.android_message_queue.put_nowait(f"ROBOT,<{self.coord['x_coord']}>,<{self.coord['y_coord']}>,<{self.coord['direction']}>")
                        
                        while self.stm_ready_recv.value != 1:
                           continue
                        
                        reverse = attempt
                        image = self.take_pic()
                        image_message = [image, f"{self.image_count.value}"]
                        print(f'[MAIN] Picture taken')
                    
                    # Stop after 3 attempts
                    elif reply in ['-1','41']  and attempt == 3:
                        #self.android_message_queue.put_nowait(f"TARGET,<{self.obstacle_id.value}>,<-1>".encode())

                        print('[MAIN] Failed to detect image, proceed to next obstacle')
                        break
                    
                    # Bulleyes condition - NOT CODED IN ALGO
                    # elif reply == '41':
                    #     image_id = f"{reply}\n"
                    #     print(f'[MAIN] Detected bullseye')
                    #     self.algo_message_queue.put_nowait(image_id.encode())
                    #     self.image_count.value += 1
                    #     break
                    
                    # Image processed    
                    else:
                        # Update android for Image Target ID on Obstacle Blocks
                        image_id = f"{reply}"
                        # print(f'[MAIN] Time taken to process image: {str(datetime.now() - start_time)} seconds')
                        self.android_message_queue.put_nowait(f"TARGET,<{self.obstacle_id.value}>,<{image_id}>")
                        break
                        
                # Decrease image count no matter what
                self.image_count.value -= 1
                
                # No more images to detect, end multiprocessing, terminate all processes
                if self.image_count.value == 0:
                    self.android_message_queue.put_nowait(b"END")

                    #self.end()
                    break
                
                 # Reverse back to original position & update android tablet
                if reverse != 0 and self.image_count.value != 0:
                    if self.direction.value == 'N':
                        self.y_coord.value = self.y_coord.value + reverse - y_count
                    elif self.direction.value == 'S':
                        self.y_coord.value = self.y_coord.value - reverse
                    elif self.direction.value == 'W':
                        self.x_coord.value = self.x_coord.value - reverse
                    elif self.direction.value == 'E':
                        self.x_coord.value = self.x_coord.value + reverse - x_count
                        
                    self.stm_ready_recv.value = 0
                    self.stm_message_queue.put_nowait(f'w0{str(reverse)}0'.encode())
                    self.android_message_queue.put_nowait(f"ROBOT,<{self.x_coord.value}>,<{self.y_coord.value}>,<{self.direction.value}>".encode())
                    
                    while self.stm_ready_recv.value != 1:
                        continue
                    
                self.algo_message_queue.put_nowait(b"DONE\n")   # Send next instructions
                    
            except Exception as error:
                print(f'[MAIN] Error Image processing!')
                raise(error)
            
        
    def _wait_processes_done(self):
        print(f'[MAIN] Client devices can attempt to re-connect with RPi')

        while True:
            try:

                if self.image_process.is_alive() or self.read_algo_process.is_alive():
                    pass
                else:
                    break

                    
            except Exception as error:
                print(f"[MAIN] Error during restarting of processes!")
                raise(error)
                