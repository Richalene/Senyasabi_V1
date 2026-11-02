
import cv2
import platform

print("Python platform:", platform.machine(), flush=True)
print("OpenCV version:", cv2.__version__, flush=True)

print("Opening camera...", flush=True)
cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)

print("Camera opened:", cap.isOpened(), flush=True)

if cap.isOpened():
    print("Reading frame...", flush=True)
    ok, frame = cap.read()
    print("Frame read:", ok, "Shape:", frame.shape if ok else None, flush=True)

cap.release()
print("Test finished.", flush=True)
