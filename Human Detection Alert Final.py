from ultralytics import YOLO
import pygame
import cv2
import numpy as np
import time
import smtplib
import os
import torch
from threading import Thread
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

# ------------------------ EMAIL CONFIG ------------------------
EMAIL = "lnithishkumar371@gmail.com"       # Your Gmail
PASSWORD = "agfb zxdw vera pbdm"           # Gmail App Password (NOT your normal password)
TARGET_EMAIL = "optimosprime51@gmail.com"  # Where you want alert emails

EMAIL_INTERVAL = 5  # seconds between summary emails


def send_email_alert(human_count, image_path=None):
    """Send a summary email: how many humans seen in last window, with optional image."""
    try:
        msg = MIMEMultipart()
        timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S")
        msg["Subject"] = f"Alert: {human_count} human(s) detected (last {EMAIL_INTERVAL}s)"
        msg["From"] = EMAIL
        msg["To"] = TARGET_EMAIL

        body_text = f"{human_count} human(s) were detected in the last {EMAIL_INTERVAL} seconds at {timestamp_str}."
        text = MIMEText(body_text, "plain")
        msg.attach(text)

        # Attach image if provided
        if image_path is not None and os.path.exists(image_path):
            with open(image_path, "rb") as f:
                img_data = f.read()
            img_part = MIMEImage(img_data, name=os.path.basename(image_path))
            msg.attach(img_part)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.send_message(msg)
        server.quit()

        print(f"📧 Email Sent: {human_count} human(s) (image: {image_path})")
    except Exception as e:
        print("❌ Email sending failed:", e)


# ------------------------ ASYNC SNAPSHOT + EMAIL ------------------------
def send_summary_async(human_count, frame_bgr):
    """
    Save snapshot + send email in a background thread so
    the main webcam loop stays smooth and non-blocking.
    """
    def worker():
        image_filename = None
        if frame_bgr is not None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            image_filename = f"capture_{timestamp}.jpg"
            saved = cv2.imwrite(image_filename, frame_bgr)
            if saved:
                print(f"📸 Snapshot saved for email: {image_filename}")
            else:
                print("❌ Failed to save snapshot image.")
                image_filename = None

        send_email_alert(human_count, image_filename)

    Thread(target=worker, daemon=True).start()  # background thread


# ------------------------ AUDIO SETUP ------------------------
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# Create a continuous beep sound once
freq = 1000
duration = 0.3
sample_rate = 44100
t = np.linspace(0, duration, int(duration * sample_rate), False)
tone = np.sin(2 * np.pi * freq * t)
audio_data = (tone * 32767 / np.max(np.abs(tone))).astype(np.int16)
audio_stereo = np.repeat(audio_data[:, np.newaxis], 2, axis=1)
beep_sound = pygame.sndarray.make_sound(audio_stereo)

beep_playing = False  # Whether the beep is currently looping

# ------------------------ YOLO SETUP ------------------------
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

model = YOLO("yolov8n.pt").to(device)  # uses GPU if available

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

conf_threshold = 0.5
person_class = 0

# For 5-second summary logic
last_email_time = time.time()
window_max_count = 0          # max number of humans seen in current 5s window
last_detection_frame = None   # last frame where humans were seen

print("Human Alert: continuous beep + 5s summary emails. Press 'q' to quit.")

# ------------------------ MAIN LOOP ------------------------
while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to read from webcam.")
        break

    # Run YOLO detection for 'person'
    results = model(frame, conf=conf_threshold, classes=[person_class], verbose=False)
    num_detected = len(results[0].boxes)
    current_detected = num_detected > 0

    # Update window stats if any humans present
    if current_detected:
        if num_detected > window_max_count:
            window_max_count = num_detected
        # remember frame for snapshot
        last_detection_frame = frame.copy()

    # Continuous beep control
    if current_detected and not beep_playing:
        beep_sound.play(loops=-1)  # loop indefinitely while human present
        beep_playing = True
    elif not current_detected and beep_playing:
        beep_sound.stop()
        beep_playing = False

    # Every EMAIL_INTERVAL seconds, send summary if any humans were seen
    now = time.time()
    if now - last_email_time >= EMAIL_INTERVAL:
        if window_max_count > 0 and last_detection_frame is not None:
            print(f"📨 Sending summary email: max {window_max_count} human(s) in last {EMAIL_INTERVAL}s")
            # Run saving + email in background
            send_summary_async(window_max_count, last_detection_frame.copy())

        # reset window for next interval
        window_max_count = 0
        last_detection_frame = None
        last_email_time = now

    # Draw annotations and current count
    annotated = results[0].plot()
    cv2.putText(
        annotated,
        f'Current humans: {num_detected}',
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    # Show video
    cv2.imshow("Human Detection Alert", annotated)

    # Quit with 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ------------------------ CLEANUP ------------------------
if beep_playing:
    beep_sound.stop()

cap.release()
cv2.destroyAllWindows()
pygame.mixer.quit()
