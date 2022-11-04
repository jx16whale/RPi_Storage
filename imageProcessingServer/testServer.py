 
import cv2
import imagezmq
import os
import torch
import numpy
import imutils
import pandas



def plot_boxes(labels, cord, frame):

        n = len(labels)
        x_shape, y_shape = frame.shape[1], frame.shape[0]
        for i in range(n):
            row = cord[i]
            # if confidence > 0.5
            if row[4] >= 0.5:
                x1, y1, x2, y2 = int(row[0]*x_shape), int(row[1]*y_shape), int(row[2]*x_shape), int(row[3]*y_shape)
                bgr = (0, 255, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), bgr, 2)
                cv2.putText(frame, str(labels[0]), (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 0.9, bgr, 2)

        return frame

print(f'Starting Server!')
RAW_IMAGE_DIR = 'raw'
image_hub = imagezmq.ImageHub()
model = torch.hub.load('ultralytics/yolov5', 'custom', path = 'best.pt')
frame_list = []



while True:  

    #cam_id, frame = image_hub.recv_image()
    ret,frame =stream.read()
    cv2.imshow('test', frame)
    frame = imutils.resize(frame, width=640)
    raw_image_name = f'frame_{str(len(frame_list))}.jpg'
    raw_image_path = os.path.join(RAW_IMAGE_DIR, raw_image_name)

    cv2.imwrite(raw_image_path,frame)
    frame = cv2.imread(raw_image_path)

    results = model(frame)
    #print(model.names)
    labels, cord = results.xyxyn[0][:, -1].numpy(), results.xyxyn[0][:, :-1].numpy()
    frame = plot_boxes(labels, cord, frame)

    processed_image_path = os.path.join('processed', raw_image_name)
    cv2.imwrite(processed_image_path, frame)
    frame_list.append(frame)
    cv2.waitKey(1)

    #image_hub.send_reply(b'OK')
  

# frame = cv2.imread('raw/3 (5).jpg')
# results = model(frame)
# labels, cord = results.xyxyn[0][:, -1].numpy(), results.xyxyn[0][:, :-1].numpy()

# # print(results.pandas().xyxy[0])
# frame = plot_boxes(labels, cord, frame)
# processed_image_path = os.path.join('processed', '3 (5).jpg')
# cv2.imwrite('processed/3 (5).jpg', frame)