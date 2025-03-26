import cv2
import tensorflow as tf
import numpy as np
import tensorflow_hub as hub
import kagglehub as kh
import math
from criteria import CRITERIA
from pushupEval import compute_pushup_angles, analyze_pushup_form
from utils import process_frame, draw_skeleton
from squatEval import evaluate_squat
# Global squat variables for counting reps and detecting depth
current_pos = "up"
squat_reps = 0
previousAngle = 0

# Download and load the MoveNet model.
path = kh.model_download("google/movenet/tensorFlow2/singlepose-lightning")
print("Path to model files:", path)
model = tf.saved_model.load(path)
movenet = model.signatures["serving_default"]

# Prompt the user to select the workout type.
workout = input("Enter workout type (Push-Up, Squat, Sit-Up): ").strip()
if workout not in CRITERIA:
    print("Workout type not recognized. Defaulting to Push-Up.")
    workout = "Push-Up"

window_name = "Workout Form Analysis - " + workout
video_path = "side-squat2.mp4"
cap = cv2.VideoCapture(0)

# Set up video recording using properties from the webcam.
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)
if fps == 0:
    fps = 30  # Fallback if FPS cannot be detected.
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('output_test.avi', fourcc, fps, (frame_width, frame_height))

frame_count = 0
feedback_list =[]
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Process frame and extract keypoints.
    keypoints = process_frame(frame,movenet)
    # Draw the skeleton (with connection labels).
    frame = draw_skeleton(frame, keypoints)

    # For push-ups, compute angles and overlay feedback.
    if workout == "Push-Up":
        angles = compute_pushup_angles(keypoints, frame.shape)
        feedback_list = analyze_pushup_form(angles, CRITERIA["Push-Up"])
        y0, dy = 30, 30
        for i, feedback in enumerate(feedback_list):
            y = y0 + i * dy
            cv2.putText(frame, feedback,(10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    if workout == "Squat":
        if frame_count % 6 ==0:
            keypoints = keypoints.squeeze()
            results, new_count, new_prevAngle, new_curr_pos = evaluate_squat(keypoints,squat_reps,previousAngle,current_pos)
            
            feedback_list = results
            squat_reps = new_count
            previousAngle = new_prevAngle
            current_pos = new_curr_pos

        rep_text = f"Reps: {squat_reps}"
        rep_position = (frame.shape[1] - 150, 50)
        cv2.putText(frame, rep_text, rep_position,
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)

        y0, dy = 30, 30
        for i, feedback in enumerate(feedback_list):
            y = y0 + i * dy
            cv2.putText(frame, feedback, (10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
        frame_count +=1

    # Write the processed frame to the output video.
    out.write(frame)
    cv2.imshow(window_name, frame)

    # Exit if 'q' is pressed or if the window is closed.
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
    if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
        break

cap.release()
out.release()
cv2.destroyAllWindows()