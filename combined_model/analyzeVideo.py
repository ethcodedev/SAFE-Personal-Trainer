import cv2
import tensorflow as tf
import numpy as np
import kagglehub as kh
from criteria import CRITERIA
from pushupEval import compute_pushup_angles, analyze_pushup_form
from utils import process_frame, draw_skeleton
from squatEval import evaluate_squat

def analyze_workout_video(input_video_path, output_video_path, workout_type="Push-Up"):
    # Load MoveNet model
    path = kh.model_download("google/movenet/tensorFlow2/singlepose-lightning")
    print("Model loaded from:", path)
    model = tf.saved_model.load(path)
    movenet = model.signatures["serving_default"]

    # Setup video capture and output
    cap = cv2.VideoCapture(input_video_path)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30  # Default fallback
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Or use 'avc1' for H264 if available
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))


    # Initialize workout-specific state
    frame_count = 0
    feedback_list = []
    squat_reps = 0
    previousAngle = 0
    current_pos = "up"

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        keypoints = process_frame(frame, movenet)
        frame = draw_skeleton(frame, keypoints)

        if workout_type == "Push-Up":
            angles = compute_pushup_angles(keypoints, frame.shape)
            feedback_list = analyze_pushup_form(angles, CRITERIA["Push-Up"])
            y0, dy = 30, 30
            for i, feedback in enumerate(feedback_list):
                y = y0 + i * dy
                cv2.putText(frame, feedback, (10, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        elif workout_type == "Squat":
            if frame_count % 6 == 0:
                keypoints = keypoints.squeeze()
                results, new_count, new_prevAngle, new_curr_pos = evaluate_squat(
                    keypoints, squat_reps, previousAngle, current_pos)
                feedback_list = results
                squat_reps = new_count
                previousAngle = new_prevAngle
                current_pos = new_curr_pos

            rep_text = f"Reps: {squat_reps}"
            rep_position = (frame.shape[1] - 150, 50)
            cv2.putText(frame, rep_text, rep_position,
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

            y0, dy = 30, 30
            for i, feedback in enumerate(feedback_list):
                y = y0 + i * dy
                cv2.putText(frame, feedback, (10, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            frame_count += 1

        out.write(frame)

    cap.release()
    out.release()
    print("Processing complete. Output saved to", output_video_path)
