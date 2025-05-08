import cv2
import mediapipe as mp
import pyautogui
import subprocess
import math
import os
import time

# Initialize MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_draw = mp.solutions.drawing_utils

# Capture webcam
cap = cv2.VideoCapture(0)

air_mouse_mode = False  # Toggle with ✌️
screen_w, screen_h = pyautogui.size()
spotify_opened = False  # Flag to track if Spotify is already opened

def finger_distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def open_spotify():
    global spotify_opened
    if not spotify_opened:
        if os.name == 'nt':
            subprocess.Popen("start spotify", shell=True)
        elif os.name == 'posix':
            subprocess.Popen(["spotify"])  # Make sure Spotify is in PATH
        spotify_opened = True  # Set the flag to True after opening Spotify
        print("Spotify opened.")

def close_spotify():
    global spotify_opened
    if spotify_opened:
        if os.name == 'nt':
            # For Windows, we'll try closing Spotify if it's open (with taskkill)
            subprocess.Popen("taskkill /f /im spotify.exe", shell=True)
        elif os.name == 'posix':
            # For Linux/macOS, killing the Spotify process (ensure Spotify is running)
            subprocess.Popen(["pkill", "spotify"])
        spotify_opened = False  # Reset the flag
        print("Spotify closed.")

last_gesture_time = 0
gesture_cooldown = 2  # seconds
last_executed = ""
gesture = ""  # Default gesture is empty

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break
    frame = cv2.flip(frame, 1)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Get landmark positions
            h, w, _ = frame.shape
            lm = hand_landmarks.landmark
            points = [(int(p.x * w), int(p.y * h)) for p in lm]

            # Extract finger tip coordinates
            thumb_tip, index_tip, middle_tip = points[4], points[8], points[12]
            thumb_ip, index_dip = points[3], points[6]
            pinky_tip = points[20]

            # Gesture recognition
            current_time = time.time()

            # Debugging: print out landmark positions for gestures
            print(f"Thumb Tip: {thumb_tip}, Index Tip: {index_tip}, Pinky Tip: {pinky_tip}")
            print(f"Time since last gesture: {current_time - last_gesture_time}")

            # Gesture checks - refined and more specific conditions
            if finger_distance(thumb_tip, index_tip) < 40:  # Pinching gesture (click)
                gesture = "Click 🤏"
            elif finger_distance(index_tip, pinky_tip) < 40:  # Mute gesture (✊)
                gesture = "Mute ✊"
            elif air_mouse_mode and finger_distance(index_tip, middle_tip) < 50:  # Air Mouse mode toggle
                gesture = "AirMouse ✌️"
            elif thumb_tip[1] < 200 and index_tip[1] < 200 and middle_tip[1] < 200:  # "Hello 👋" gesture
                gesture = "Hello 👋"

            # Gesture cooldown check to ensure no rapid repeated gestures
            if gesture and (gesture != last_executed or (current_time - last_gesture_time > gesture_cooldown)):
                last_executed = gesture
                last_gesture_time = current_time

                print(f"Gesture detected: {gesture}")

                # Execute corresponding actions based on gesture
                if gesture == "Hello 👋":
                    open_spotify()  # Open Spotify only once
                elif gesture == "Next 👉":
                    pyautogui.press("nexttrack")
                elif gesture == "Mute ✊":
                    pyautogui.press("volumemute")
                elif gesture == "AirMouse ✌️":
                    air_mouse_mode = not air_mouse_mode
                elif gesture == "Click 🤏":
                    pyautogui.click()

                # Display gesture on screen
                cv2.putText(frame, gesture, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)

            # Air Mouse Mode
            if air_mouse_mode:
                x, y = index_tip
                screen_x = int(x * screen_w / w)
                screen_y = int(y * screen_h / h)
                pyautogui.moveTo(screen_x, screen_y)
                # Click when thumb & index are pinched
                if finger_distance(index_tip, thumb_tip) < 40:
                    pyautogui.click()
                    gesture = "Click 🤏"

            # Show gesture label
            if gesture:
                cv2.putText(frame, gesture, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)

    # Display window
    cv2.imshow("Gesture-to-App Automator", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()