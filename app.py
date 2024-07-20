from flask import Flask, render_template, Response
import cv2
import time
import threading
import pygame

app = Flask(__name__)

# Load the cascade for eye detection
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

# Initialize pygame for sound
pygame.mixer.init()

eye_closed_start_time = None
eye_closed_duration_threshold = 3  # seconds

def play_sound():
    pygame.mixer.music.load("alert.mp3")  # Make sure to have an alert.mp3 file in your working directory
    pygame.mixer.music.play()

def gen_frames():
    global eye_closed_start_time
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        exit()

    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            eyes = eye_cascade.detectMultiScale(gray, 1.3, 5)

            if len(eyes) == 0:
                if eye_closed_start_time is None:
                    eye_closed_start_time = time.time()
                else:
                    eye_closed_duration = time.time() - eye_closed_start_time
                    if eye_closed_duration > eye_closed_duration_threshold:
                        threading.Thread(target=play_sound).start()
                        eye_closed_start_time = time.time()
            else:
                eye_closed_start_time = None

            for (ex, ey, ew, eh) in eyes:
                cv2.rectangle(frame, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True)
