import cv2


camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("Could not open webcam.")
    raise SystemExit

print("Camera test running. Press ESC to quit.")

while True:
    success, frame = camera.read()

    if not success:
        print("Could not read webcam frame.")
        break

    cv2.imshow("Camera Test", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

camera.release()
cv2.destroyAllWindows()
