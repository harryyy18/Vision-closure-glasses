import cv2
import time
import winsound
import pyttsx3
import matplotlib.pyplot as plt
from datetime import datetime
from tkinter import Tk, Label, Button, filedialog, messagebox, Scale, HORIZONTAL, simpledialog
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
from twilio.rest import Client
import os
import serial  # For serial communication, if needed
  # If using serial devices for heart rate sensor

# Firebase initialization
cred = credentials.Certificate(r"C:\Users\harry\OneDrive\Desktop\Projects\selfalert-2004-firebase-adminsdk-fbsvc-24199bd8f5.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Twilio credentials (loaded from environment variables or a secure file)
twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID", "ACfccc9a61255b6d2be603f33d91c2ba5d")
twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN", "137aeeb2a599123b5b13d9d5a736cc7b")
twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER", "+15677042196")
recipient_number = os.getenv("RECIPIENT_PHONE_NUMBER", "+918200287696")

# Haar cascade for eye detection
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

# Initialize variables
cap = cv2.VideoCapture(0)
eye_closed_start_time = None
eye_closed_duration_threshold = 2  # Default threshold in seconds
silent_mode = False
time_stamps = []
closure_times = []
user_profiles = {}
current_user = "default"

# Initialize pyttsx3 for voice alerts
engine = pyttsx3.init()

# Function to play a sound alert
def play_sound():
    if not silent_mode:
        winsound.Beep(1000, 1000)

# Function to send an SMS alert
def send_sms_alert(duration):
    try:
        client = Client(twilio_account_sid, twilio_auth_token)
        message = client.messages.create(
            body=f"Alert! Eye closure detected for {duration:.2f} seconds.",
            from_=twilio_phone_number,
            to=recipient_number
        )
        print(f"SMS sent: {message.sid}")
    except Exception as e:
        print(f"Error sending SMS: {e}")

# Function to log data to Firebase
def log_eye_closure_to_firebase(duration):
    try:
        doc_ref = db.collection("eye_closures").document()
        doc_ref.set({
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "user": current_user
        })
        print("Eye closure data logged to Firebase")
    except Exception as e:
        print(f"Error logging to Firebase: {e}")

# Function to update the real-time graph
def update_graph(duration):
    time_stamps.append(time.strftime('%H:%M:%S'))
    closure_times.append(duration)

    # Limit graph size
    if len(time_stamps) > 100:
        time_stamps.pop(0)
        closure_times.pop(0)

    plt.clf()
    plt.plot(time_stamps, closure_times, label='Eye Closure Duration', marker='o', color='blue', linewidth=2)
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.xlabel('Time', fontsize=12, fontweight='bold')
    plt.ylabel('Duration (seconds)', fontsize=12, fontweight='bold')
    plt.title('Real-Time Eye Closure Duration', fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.legend()
    try:
        plt.pause(0.1)
    except Exception as e:
        print(f"Graph update error: {e}")

# Function to retrieve historical data from Firebase
def view_history():
    try:
        docs = db.collection("eye_closures").where("user", "==", current_user).stream()
        data = []
        for doc in docs:
            record = doc.to_dict()
            data.append({
                "Timestamp": record.get("timestamp", "N/A"),
                "Duration": record.get("duration", 0)
            })

        df = pd.DataFrame(data)
        if not df.empty:
            df["Timestamp"] = pd.to_datetime(df["Timestamp"])
            df.sort_values(by="Timestamp", inplace=True)
            print("Historical Data:")
            print(df)

            df.plot(x="Timestamp", y="Duration", kind="line", marker='o', title="Eye Closure History")
            plt.xlabel("Timestamp")
            plt.ylabel("Duration (seconds)")
            plt.grid(True)
            plt.show()
        else:
            messagebox.showinfo("Info", "No historical data available.")
    except Exception as e:
        print(f"Error retrieving historical data: {e}")

# Function to process each frame
def process_frame(frame):
    global eye_closed_start_time

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    eyes = eye_cascade.detectMultiScale(gray, 1.3, 5)

    if len(eyes) == 0:
        if eye_closed_start_time is None:
            eye_closed_start_time = time.time()
        else:
            duration = time.time() - eye_closed_start_time
            if duration > eye_closed_duration_threshold:
                # Alert mechanisms
                play_sound()
                engine.say("Warning! Your eyes have been closed for too long.")
                engine.runAndWait()
                send_sms_alert(duration)
                log_eye_closure_to_firebase(duration)
                update_graph(duration)
                eye_closed_start_time = None
    else:
        eye_closed_start_time = None

    for (ex, ey, ew, eh) in eyes:
        cv2.rectangle(frame, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)

# Function to switch user profiles
def switch_user_profile(new_user):
    global current_user, eye_closed_duration_threshold
    current_user = new_user
    eye_closed_duration_threshold = user_profiles.get(current_user, eye_closed_duration_threshold)
    print(f"Switched to user profile: {current_user}")

# Function to export historical data
def export_data():
    try:
        docs = db.collection("eye_closures").where("user", "==", current_user).stream()
        data = []
        for doc in docs:
            record = doc.to_dict()
            data.append({"Timestamp": record.get("timestamp", "N/A"), "Duration": record.get("duration", 0)})

        df = pd.DataFrame(data)
        if not df.empty:
            file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
            if file_path:
                df.to_csv(file_path, index=False)
                messagebox.showinfo("Success", "Data exported successfully!")
        else:
            messagebox.showinfo("Info", "No data to export.")
    except Exception as e:
        print(f"Error exporting data: {e}")

# Enhanced function for inactivity timeout
def check_inactivity(start_time, timeout_duration=60):
    if time.time() - start_time > timeout_duration:
        print("Inactivity detected. Shutting down camera and GUI.")
        cap.release()
        cv2.destroyAllWindows()
        plt.ioff()
        plt.show()
        os._exit(0)

# Main function for detection
def start_detection():
    global silent_mode
    print("Starting detection. Press 'q' to quit.")

    plt.ion()  # Turn on interactive plotting
    plt.figure(figsize=(10, 5))
    last_interaction_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame.")
                break

            process_frame(frame)
            cv2.imshow('Eye Detector', frame)

            # Check for inactivity
            check_inactivity(last_interaction_time, timeout_duration=120)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        plt.ioff()
        plt.show()

# GUI for advanced options
def create_gui():
    def toggle_silent_mode():
        global silent_mode
        silent_mode = not silent_mode
        status_label.config(text=f"Silent Mode: {'ON' if silent_mode else 'OFF'}")

    def adjust_threshold(val):
        global eye_closed_duration_threshold
        eye_closed_duration_threshold = int(val)

    def switch_profile():
        new_user = simpledialog.askstring("Switch Profile", "Enter new profile name:")
        if new_user:
            switch_user_profile(new_user)

    root = Tk()
    root.title("Eye Closure Detection")

    Label(root, text="Eye Closure Detection System", font=("Arial", 16, "bold")).pack(pady=10)

    Button(root, text="Start Detection", font=("Arial", 14), command=start_detection).pack(pady=10)
    Button(root, text="View History", font=("Arial", 14), command=view_history).pack(pady=10)
    Button(root, text="Export Data", font=("Arial", 14), command=export_data).pack(pady=10)
    Button(root, text="Switch Profile", font=("Arial", 14), command=switch_profile).pack(pady=10)
    Button(root, text="Toggle Silent Mode", font=("Arial", 14), command=toggle_silent_mode).pack(pady=10)

    Label(root, text="Adjust Threshold (seconds):", font=("Arial", 12)).pack(pady=5)
    threshold_slider = Scale(root, from_=1, to_=10, orient=HORIZONTAL, font=("Arial", 12), command=adjust_threshold)
    threshold_slider.set(eye_closed_duration_threshold)
    threshold_slider.pack(pady=10)

    status_label = Label(root, text="Silent Mode: OFF", font=("Arial", 12))
    status_label.pack(pady=5)

    root.mainloop()

# Run the GUI
if __name__ == "__main__":
    user_profiles = {"default": 3, "driver": 2, "student": 5}  # Example profiles
    create_gui()
