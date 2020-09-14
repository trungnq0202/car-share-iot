from imutils.video import VideoStream
from imutils.video import FPS
import face_recognition
import numpy as np
import argparse
import imutils
import pickle
import time
import cv2
import os
import time

# ap = argparse.ArgumentParser()
# ap.add_argument("-d", "--detector", required=True)
# #ap.add_argument("-m", "--embedding_model", required=True)
# ap.add_argument("-r", "--recognizer", required=True)
# ap.add_argument("-l", "--le", required=True)
# ap.add_argument("-c", "--confidence", type=float, default=0.5)
# args = vars(ap.parse_args())

DEPLOY_PROTOTXT_PATH = 'facial_recognition/pretrained_model/deploy.prototxt'
RES10_300X300_PATH = 'facial_recognition/pretrained_model/res10_300x300_ssd_iter_140000.caffemodel'
RECOGNIZER_PATH = 'facial_recognition/output/recognizer.pickle'
LABEL_ENCODER_PATH = 'facial_recognition/output/le.pickle'
CONFIDENCE = 0.5

# print("[INFO] loading face detector...")
# protoPath = os.path.sep.join([args["detector"], "deploy.prototxt"])
# modelPath = os.path.sep.join([args["detector"],
#   "res10_300x300_ssd_iter_140000.caffemodel"])
def recognize():
    detector = cv2.dnn.readNetFromCaffe(DEPLOY_PROTOTXT_PATH, RES10_300X300_PATH)
    
    #print("[INFO] loading face recognizer...")
    #embedder = cv2.dnn.readNetFromTorch(args["embedding_model"])

    recognizer = pickle.loads(open(RECOGNIZER_PATH, "rb").read())
    le = pickle.loads(open(LABEL_ENCODER_PATH, "rb").read())

    print("[INFO] starting video stream...")
    vs = VideoStream(src=0).start()
    time.sleep(2.0)

    fps = FPS().start()
    tstart = time.time()

    while True:
        frame = vs.read()
        frame = imutils.resize(frame, width=600)

        (h, w) = frame.shape[:2]

        imageBlob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)), 1.0, (300, 300),
            (104.0, 177.0, 123.0), swapRB=False, crop=False)

        detector.setInput(imageBlob)
        detections = detector.forward()

        for i in range(0, detections.shape[2]):
            confidence = detections[0, 0, i, 2]

            if confidence > CONFIDENCE:
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")

                face = frame[startY:endY, startX:endX]
                (fH, fW) = face.shape[:2]

                if fW < 20 or fH < 20:
                    continue

                #faceBlob = cv2.dnn.blobFromImage(face, 1.0 / 255,
                #   (96, 96), (0, 0, 0), swapRB=True, crop=False)
                #embedder.setInput(faceBlob)
                #vec = embedder.forward()
                coor = [((startY, startX + (endX - startX), startY + (endY - startY), startX))]
            
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                encodings = face_recognition.face_encodings(rgb_frame, coor)

                preds = recognizer.predict_proba(encodings)[0]
                j = np.argmax(preds)
                proba = preds[j]
                name = le.classes_[j]

                text = "{}: {:.2f}%".format(name, proba * 100)
                y = startY - 10 if startY - 10 > 10 else startY + 10
                cv2.rectangle(frame, (startX, startY), (endX, endY),
                    (0, 0, 255), 2)
                cv2.putText(frame, text, (startX, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 2)

        fps.update()

        cv2.imshow("Frame", frame)
        # tcur = time.time()

        # if tcur - tstart > 15 & name != 'unknown' & proba > 0.8:
        #     return name
        # elif tcur - tstart > 60:
        #     return 'unknown'

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

    fps.stop()
    print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
    print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

    cv2.destroyAllWindows()
    vs.stop()
