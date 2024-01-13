import cv2

# Open the default camera
cap = cv2.VideoCapture(0)

while True:
    # Read the current frame from the camera
    ret, frame = cap.read()

    # Display the frame
    cv2.imshow('Camera', frame)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the camera and close the window
cap.release()
cv2.destroyAllWindows()