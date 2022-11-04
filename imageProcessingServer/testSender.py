from imutils.video import VideoStream
import cv2
import imagezmq
import time
import socket

name = socket.gethostname()
sender = imagezmq.ImageSender(connect_to='tcp://192.168.0.73:5555')

frameWidth = 1920   
frameHeight = 1080
cap = cv2.VideoCapture(0)
cap.set(3,frameWidth)
cap.set(4,frameHeight)
# vs = VideoStream(usePiCamera=True).start()
# time.sleep(2)

    # img = vs.read()
success, img = cap.read()
    
if success:
    sender.send_image(name,img)

    # showing result, it take frame name and image 
    # output
    # cv2.imshow("GeeksForGeeks", img)
  

    # If keyboard interrupt occurs, destroy image 
    # # window
    # cv2.waitKey(0)
    # cv2.destroyWindow("GeeksForGeeks")
    sender.close()
# If captured image is corrupted, moving to else part
else:
    print("No image detected. Please! try again")    
# cv2.release()
# cv2.destroyAllWindows()
