import cv2
import time
import winsound

# Load the cascade for eye detection
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

# Capture video from webcam
cap = cv2.VideoCapture(0)

eye_closed_start_time = None
eye_closed_duration_threshold = 3  # seconds

def play_sound():
    winsound.Beep(1000, 1000)  # Frequency: 1000 Hz, Duration: 1000 ms (1 second)

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect eyes
    eyes = eye_cascade.detectMultiScale(gray, 1.3, 5)

    # Check if eyes are detected
    if len(eyes) == 0:
        if eye_closed_start_time is None:
            eye_closed_start_time = time.time()
        else:
            eye_closed_duration = time.time() - eye_closed_start_time
            if eye_closed_duration > eye_closed_duration_threshold:
                play_sound()
                # Reset the timer after playing the sound to avoid continuous beeping
                eye_closed_start_time = time.time()
    else:
        eye_closed_start_time = None
    
    # Draw rectangles around detected eyes
    for (ex, ey, ew, eh) in eyes:
        cv2.rectangle(frame, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)

    # Display the resulting frame
    cv2.imshow('Eye Detector', frame)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture and close windows
cap.release()
cv2.destroyAllWindows()
