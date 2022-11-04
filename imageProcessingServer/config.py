# Encoding / Decoding format
# FORMAT = "utf-8"

#Android BT connection settings

RFCOMM_CHANNEL = 1
RPI_MAC_ADDR = ''
UUID = '00001101-0000-1000-8000-00805F9B34FB'
ANDROID_SOCKET_BUFFER_SIZE = 1024

# Algorithm Wifi connection settings
WIFI_IP = '192.168.15.1'
WIFI_PORT = 8080
ALGO_SOCKET_BUFFER_SIZE = 1024

# STM USB connection settings
# Symbolic link to always point to the correct port that STM is connected to
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 115200

# Image Recognition Settings
# IMAGE_WIDTH = 1920
# IMAGE_HEIGHT = 1080
# IMAGE_WIDTH = 1280
# IMAGE_HEIGHT = 720
IMAGE_WIDTH = 640
IMAGE_HEIGHT = 480
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