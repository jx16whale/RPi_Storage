import os, shutil
import time
import cv2
import torch
from imagezmq import ImageHub
from datetime import datetime
from protocol import *


class CustomImageHub(ImageHub):
    def send_reply(self, reply_message):
        """Sends the zmq REP reply message.
        Arguments:
          reply_message: reply message text, often just string 'OK'
        """
        reply_message = reply_message.encode('utf-8')
        self.zmq_socket.send(reply_message)


class ImageProcessingServer:
    def __init__(self):
        
        self.image_hub = CustomImageHub()
        self.model = torch.hub.load('ultralytics/yolov5', 'custom', path='best_150epochs.onnx')

        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.classes = self.model.names
        
        self.initialise_directories()
        self.frame_list = []  # list of frames with detections
        
    def start(self):
        # keep track of recognised classes
        self.recognised_class = []
        while True:
            try:
                self.model.to(self.device)
                #
                self.model.classes = [21, 24, 26, 27]
                print(f"Incoming Image...")
                start = datetime.now()
                rpi_name, frame = self.image_hub.recv_image()
                print(f'Received at time : {str(datetime.now())}')
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                raw_image_name = RAW_IMAGE_PREFIX + str(len(self.frame_list)) + IMAGE_ENCODING
                raw_image_path = os.path.join(self.raw_dir, raw_image_name)
                cv2.imwrite(raw_image_path, frame)
          
                print("------ Starting detection ------")
                
                # default values
                reply = '-1'
                conf_thr = 0
                
                
                results = self.model(raw_image_path)
                
                # get labels and coordinates
                labels, coord = results.xyxyn[0][:, -1].numpy(), results.xyxyn[0][:, :-1].numpy()
               # print(len(labels))
                #n = len(labels)  
                # for i in range(n):
                #     label = int(float(labels[i]))
                #     print(f"{type(label)} {str(label)}")
                #     currentClass = self.classes[label]
                #     # next time 41
                #     if currentClass not in self.recognised_class:
                #         if currentClass == 'bullseye':
                #             break
                #         else:
                #             conf_thr = coord[i]
                #             if conf_thr[4] >= MIN_CONFIDENCE_THRESHOLD:
                #                 frame = self.plot_boxes(frame, label, conf_thr)
                #                 self.recognised_class.append(currentClass) 
                #                 reply = str(label)
                
                # get only the first detected class (sorted by highest conf)
                if(len(labels) > 0):
                    label = int(float(labels[0]))
                    print(f"{type(label)} {str(label)}")
                    currentClass = self.classes[label]
                    print(currentClass)
                    
                    # hard code to correct the label
                    new_label = self.correct_label(label)

                    reply = str(new_label)
                    # next time 41
                
                    if reply != '41':
                        conf_thr = coord[0]
                        self.image_hub.send_reply(reply)
                        print(f'[MAIN] Time taken to process picture: {str(datetime.now() - start)} seconds')
                        self.frame_list.append(frame) 
                        print('confidence level : ', conf_thr[4])
                        if conf_thr[4] >= MIN_CONFIDENCE_THRESHOLD:
                            frame = self.plot_boxes(frame, label, new_label, conf_thr)
                            self.recognised_class.append(currentClass)
                            processed_image_name = PROCESSED_IMAGE_PREFIX + str(len(self.frame_list)) + IMAGE_ENCODING
                            processed_image_path = os.path.join(self.processed_dir, processed_image_name)
                            cv2.imwrite(processed_image_path, frame)
                            img = cv2.imread(processed_image_path)
                           # cv2.imshow("processed", img)
                        else:
                            reply = '-1'   
                        
                if reply == '-1':
                    self.image_hub.send_reply(reply)
                    self.frame_list.append(frame) 
                    print(f"No image detected")
                elif reply == '41':
                    self.image_hub.send_reply(reply)
                    self.frame_list.append(frame) 
                    print(f"Detected bullseye")
                    
                else:
                    pass

                
          #      self.image_hub.send_reply(reply)
           #     self.frame_list.append(frame) 
                
                #self.terminate()  

                
            except KeyboardInterrupt:
                print("User has pressed ctrl-c button")
                break
                
    def plot_boxes(self, frame, label, new_label, conf_thr):
        """
        Takes a frame and its results as input, and plots the bounding boxes and label on to the frame.
        :param results: contains labels and coordinates predicted by model on the given frame.
        :param frame: Frame which has been scored.
        :return: Frame with bounding boxes and labels ploted on it.
        """
          
        x_shape, y_shape = frame.shape[1], frame.shape[0]  
        
        x1, y1, x2, y2 = int(conf_thr[0]*x_shape), int(conf_thr[1]*y_shape), int(conf_thr[2]*x_shape), int(conf_thr[3]*y_shape)

        bgr = (0, 255, 0)
        cv2.rectangle(frame, (x1, y1), (x2, y2), bgr, 2)
        cv2.putText(frame, f'{self.classes[label]}, IMG_ID: {str(new_label)}', (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 0.9, bgr, 2)
        #cv2.putText(frame, str(label), (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 0.9, bgr, 2)
        
        return frame       
    
    
    
    def terminate(self):
        print(f'Terminating image processing server...')
        self.image_hub.send_reply('OK')
        # send_reply disconnects the connection
        print(f'Image Server terminated at time: {str(datetime.now())}')
    
    
    def initialise_directories(self):
        self.cwdir = os.path.dirname(os.path.realpath(__file__))


        self.raw_dir = os.path.join(self.cwdir, RAW_IMAGE_DIR)
        if not os.path.exists(self.raw_dir):
            os.makedirs(self.raw_dir)

        self.processed_dir = os.path.join(self.cwdir, PROCESSED_IMAGE_DIR)
        if not os.path.exists(self.processed_dir):
            os.makedirs(self.processed_dir)

    def correct_label(self, label):
        if label==0:
            return 20
        elif label==1:
            return 21
        elif label==2:
            return 22
        elif label==3:
            return 23
        elif label==4:
            return 24
        elif label==5:
            return 25
        elif label==6:
            return 26
        elif label==7:
            return 27
        elif label==8:
            return 28
        elif label==9:
            return 29
        elif label==10:
            return 30
        elif label==11:
            return 31
        elif label==12:
            return 32
        elif label==13:
            return 33
        elif label==14:
            return 34
        elif label==15:
            return 35
        elif label==23:
            return 11
        elif label == 29:
            return 12
        elif label==28:
            return 13
        elif label == 20:
            return 14
        elif label==19:
            return 15
        elif label == 26:
            return 39
        elif label==25:
            return 17
        elif label == 18:
            return 18
        elif label == 22:
            return 19
        elif label== 30:
            return 36
        elif label == 27:
            return 38
        elif label == 21:
            return 39
        elif label == 24:
            return 38
        elif label == 16: 
            return 41
        elif label == 17:
            return 37
        else: 
            return label

        # left arrow : 39
        # right arrow : 38

        







if __name__ == '__main__':
    image_hub = ImageProcessingServer()
    image_hub.start()











# imageHub = imagezmq.ImageHub()

# while True:
#     try:
#         print('[Image Server] Waiting for image from RPi')
#         rpiName, frame = imageHub.recv_image()
#         cv2.imshow(rpiName, frame)
#         cv2.imwrite("raw/test.jpg", frame)
#         cv2.waitKey(1)
#         imageHub.send_reply(b'OK')
#     except KeyboardInterrupt as e:
#                 print("[Image Server] Ctrl-C")
#                 break