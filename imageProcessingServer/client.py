#from imutils.video import VideoStream
import imagezmq
import argparse
import socket
import time
import picamera

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-s", "--server-ip", required=True,
	help="ip address of the server to which the client will connect")
args = vars(ap.parse_args())
# initialize the ImageSender object with the socket address of the
# server
sender = imagezmq.ImageSender(connect_to=f"tcp://{args["server_ip"]}:5555")

# get the host name, initialize the video stream, and allow the
# camera sensor to warmup
rpiName = socket.gethostname()
camera = PiCamera(resolution=(1920, 1080))
camera.iso = 700
rawCapture = PiRGBArray(camera)
time.sleep(0.2)
camera.capture(rawCapture, format='bgr')
image = rawCapture.array
#image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
camera.close()
#vs = VideoStream(usePiCamera=True).start()
#vs = VideoStream(src=0).start()
time.sleep(2.0)
 
# while True:
# 	# read the frame from the camera and send it to the server
# 	frame = vs.read()
sender.send_image(rpiName, image)