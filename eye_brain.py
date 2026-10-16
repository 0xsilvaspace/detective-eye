import os
import warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
warnings.filterwarnings('ignore')

print("--- STEP 1: Importing Libraries... ---")
import cv2
import mediapipe as mp
import serial
import time
import math
import numpy as np
from sklearn.cluster import KMeans

SERIAL_PORT = 'COM8'   
BAUD_RATE = 115200
CAM_ID = 0
SMOOTHING = 0.3 

print("--- STEP 2: Connecting to Arduino... ---")
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2) 
    print(f"SUCCESS: Connected to {SERIAL_PORT}")
except:
    print("WARNING: Arduino not found. Simulation Mode.")
    ser = None

mp_face_detection = mp.solutions.face_detection
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

face_detection = mp_face_detection.FaceDetection(min_detection_confidence=0.7)
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.8)

current_x, current_y = 90, 15
last_color_update = 0
cached_color_text = "Scanning..."
prev_wrist_x = 0
wave_score = 0 
face_was_present = False
doing_scan = False
scan_animation_start = 0

def map_range(x, in_min, in_max, out_min, out_max):
    val = (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    return max(min(val, out_max), out_min)

def closest_color_name(rgb):
    r, g, b = rgb

    colors = {
        "Black": [30, 30, 30], "White": [220, 220, 220], "Grey": [128, 128, 128],
        "Red": [200, 40, 40], "Green": [40, 200, 40], "Blue": [20, 20, 180],
        "Yellow": [220, 220, 40], "Orange": [220, 140, 20], "Purple": [128, 0, 128],
        "Navy": [10, 10, 80], "Brown": [100, 60, 30]
    }
    min_dist = float('inf')
    best_match = "Unknown"
    for name, val in colors.items():
        dist = math.sqrt((r - val[0])**2 + (g - val[1])**2 + (b - val[2])**2)
        if dist < min_dist:
            min_dist = dist
            best_match = name
    return best_match

def analyze_shirt_advanced(image, face_bbox):
    h, w, _ = image.shape
    x, y = int(face_bbox.xmin * w), int(face_bbox.ymin * h)
    fw, fh = int(face_bbox.width * w), int(face_bbox.height * h)
    
    chest_y_start = min(y + fh + int(fh * 0.4), h - 1)
    chest_y_end = min(y + fh + int(fh * 0.9), h - 1)
    chest_x_start = max(x + int(fw * 0.35), 0) 
    chest_x_end = min(x + fw - int(fw * 0.35), w)

    if chest_y_end - chest_y_start < 10 or chest_x_end - chest_x_start < 10: 
        return "Hidden"

    chest_roi = image[chest_y_start:chest_y_end, chest_x_start:chest_x_end]
    
    invGamma = 1.0 / 1.2
    table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    chest_roi = cv2.LUT(chest_roi, table)

    small_roi = cv2.resize(chest_roi, (50, 50)) 
    small_roi = cv2.cvtColor(small_roi, cv2.COLOR_BGR2RGB)
    pixels = small_roi.reshape((-1, 3))
    
    try:
        kmeans = KMeans(n_clusters=1, n_init=5)
        kmeans.fit(pixels)
        name = closest_color_name(kmeans.cluster_centers_[0])
        cv2.rectangle(image, (chest_x_start, chest_y_start), (chest_x_end, chest_y_end), (0, 255, 255), 2)
        return name
    except: return "Error"

print("--- STEP 4: Opening Camera... ---")
cap = cv2.VideoCapture(CAM_ID)

while cap.isOpened():
    success, image = cap.read()
    if not success: break

    image = cv2.flip(image, 1)
    h, w, c = image.shape
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    face_results = face_detection.process(rgb_image)
    hand_results = hands.process(rgb_image)
    
    target_x, target_y = None, None
    gesture_text = "None"
    tracking_mode = "None"
    has_face = False

    if face_results.detections:
        has_face = True
       
        primary_detection = max(face_results.detections, key=lambda d: d.location_data.relative_bounding_box.width * d.location_data.relative_bounding_box.height)
        
        mp_drawing.draw_detection(image, primary_detection)
        bbox = primary_detection.location_data.relative_bounding_box
        
        target_x = (bbox.xmin + bbox.width/2) * w
        target_y = (bbox.ymin + bbox.height/2) * h
        tracking_mode = "Face"
        
        if not face_was_present:
            doing_scan = True
            scan_animation_start = time.time()
            face_was_present = True
        
        if time.time() - last_color_update > 1.0:
            cached_color_text = analyze_shirt_advanced(image, bbox)
            last_color_update = time.time()
    else:
        face_was_present = False 
        doing_scan = False

    if hand_results.multi_hand_landmarks:
        hand_list = hand_results.multi_hand_landmarks
        for hand_lms in hand_list:
             mp_drawing.draw_landmarks(image, hand_lms, mp_hands.HAND_CONNECTIONS)

        if len(hand_list) == 2:
            h1 = hand_list[0].landmark[9]
            h2 = hand_list[1].landmark[9]
            if math.hypot(h1.x - h2.x, h1.y - h2.y) < 0.15:
                gesture_text = "Handshake!"
        
        
        if gesture_text == "None":
            hand_lms = hand_list[0] 
            
            fingers = []
            if hand_lms.landmark[4].x < hand_lms.landmark[3].x: fingers.append(1)
            else: fingers.append(0)
            
            for tip in [8, 12, 16, 20]:
                if hand_lms.landmark[tip].y < hand_lms.landmark[tip - 2].y: fingers.append(1)
                else: fingers.append(0)
            
            wrist_x = hand_lms.landmark[0].x
            movement = abs(wrist_x - prev_wrist_x) * 100 
            prev_wrist_x = wrist_x 
            if sum(fingers) == 5 and movement > 3.0: wave_score += 1
            else: wave_score = max(0, wave_score - 1)
            
           
            thumb_tip_y = hand_lms.landmark[4].y
            index_tip_y = hand_lms.landmark[8].y
            thumb_knuckle_y = hand_lms.landmark[2].y

            if wave_score > 5: gesture_text = "Waving!"
            elif sum(fingers) == 5: gesture_text = "Hello"
            elif sum(fingers) == 0: gesture_text = "Chop Knuckles"
            
            
            elif fingers[0] == 1 and sum(fingers[1:]) == 0 and thumb_tip_y < thumb_knuckle_y: 
                gesture_text = "Thumbs Up"
            
            elif fingers[1] == 1 and sum(fingers[2:]) == 0: 
                gesture_text = "Pointing"
                
            elif fingers == [0, 1, 1, 0, 0] or fingers == [1, 1, 1, 0, 0]: 
                gesture_text = "Peace"
            else: 
                gesture_text = "Reading Gesture"

        
        if target_x is None: 
            target_x = hand_list[0].landmark[9].x * w
            target_y = hand_list[0].landmark[9].y * h  
            tracking_mode = "Hand"

    if target_x is not None:
        tx = map_range(target_x, 0, w, 20, 160)
        
        if tracking_mode == "Face":
           
            ty = map_range(target_y, 0, h, 10, 40) 
            
            if doing_scan:
                elapsed = time.time() - scan_animation_start
                if elapsed < 0.5: ty = 50  
                elif elapsed < 1.0: ty = 10 
                else: doing_scan = False   
                gesture_text = "Scanning..."

        elif tracking_mode == "Hand":
            
            ty = map_range(target_y, 0, h, 10, 40) 
            gesture_text += " (Tracking)"

        current_x = (current_x * SMOOTHING) + (tx * (1 - SMOOTHING))
        current_y = (current_y * SMOOTHING) + (ty * (1 - SMOOTHING))
        
        if ser: ser.write(f"X{int(current_x)}Y{int(current_y)}\n".encode())

  
    cv2.rectangle(image, (0, 0), (w, 80), (0, 0, 0), -1)
    
    display_shirt = cached_color_text if has_face else "No Face"
    cv2.putText(image, f"Shirt: {display_shirt}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    cv2.putText(image, f"Gesture: {gesture_text}", (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    cv2.imshow('Robot Vision V12 (Final)', image)
    if cv2.waitKey(5) & 0xFF == 27: break

cap.release()
cv2.destroyAllWindows()