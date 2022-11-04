# Encoding / Decoding format
# FORMAT = "utf-8"

#Android BT connection settings

RFCOMM_CHANNEL = 1
RPI_MAC_ADDR = ''
UUID = '00001101-0000-1000-8000-00805F9B34FB'
#UUID = '94f39d29-7d6d-437d-973b-fba39e49d4ee'
#UUID = '87b585d1-84c3-486a-8f3d-77cf16f84f30'
#UUID = '443559ba-b89f-4fb6-99d9-ddbcd6138fbd'
ANDROID_SOCKET_BUFFER_SIZE = 1024

# Algorithm Wifi connection settings
WIFI_IP = '192.168.15.1'
WIFI_PORT = 8080
ALGO_SOCKET_BUFFER_SIZE = 1024

# STM USB connection settings
# Symbolic link to always point to the correct port that STM is connected to
SERIAL_PORT = ['/dev/ttyUSB0','/dev/ttyUSB1']
BAUD_RATE = 115200

# Image Recognition Settings
IMAGE_WIDTH = 1920
IMAGE_HEIGHT = 1080
IMAGE_FORMAT = 'bgr'
IMAGE_SERVER_ADDR = (WIFI_IP, WIFI_PORT)
BASE_IP = 'tcp://192.168.15.'
IMAGE_PORT = ':5555'
MIN_CONFIDENCE_THRESHOLD = 0.50
RAW_IMAGE_PREFIX = 'frame'
PROCESSED_IMAGE_PREFIX = 'processed'
RAW_IMAGE_DIR = 'raw'
PROCESSED_IMAGE_DIR = 'processed'
IMAGE_ENCODING = '.jpg'