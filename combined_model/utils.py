import cv2
import tensorflow as tf
import numpy as np
import tensorflow_hub as hub
JOINT_LABELS = {
    0: "Nose",
    1: "Left Eye",
    2: "Right Eye",
    3: "Left Ear",
    4: "Right Ear",
    5: "Left Shoulder",
    6: "Right Shoulder",
    7: "Left Elbow",
    8: "Right Elbow",
    9: "Left Wrist",
    10: "Right Wrist",
    11: "Left Hip",
    12: "Right Hip",
    13: "Left Knee",
    14: "Right Knee",
    15: "Left Ankle",
    16: "Right Ankle"
}
def process_frame(frame,movenet):
    """Resizes the frame, runs inference with MoveNet, and returns keypoints."""
    input_tensor = tf.image.resize(frame, (192, 192))
    input_tensor = tf.cast(input_tensor, dtype=tf.int32)
    input_tensor = tf.expand_dims(input_tensor, axis=0)
    outputs = movenet(input_tensor)
    keypoints = outputs["output_0"].numpy()  # Shape: (1, 1, 17, 3)
    return keypoints

def draw_skeleton(frame, keypoints, threshold=0.3):
    """
    Draws keypoints and connects them with lines to form a skeleton.
    Labels are added at the midpoint of each connection.
    Assumes keypoints are in normalized coordinates with shape (1, 1, 17, 3).
    """
    height, width, _ = frame.shape
    kpts = keypoints[0, 0, :, :]  # Shape: (17, 3)

    # Define skeleton connections (based on MoveNet keypoint indices).
    skeleton_connections = [
        (0, 1), (0, 2),       # Nose to eyes
        (1, 3), (2, 4),       # Eyes to ears
        (0, 5), (0, 6),       # Nose to shoulders
        (5, 7), (7, 9),       # Left arm (shoulder -> elbow -> wrist)
        (6, 8), (8, 10),      # Right arm (shoulder -> elbow -> wrist)
        (5, 6),               # Shoulders
        (5, 11), (6, 12),     # Shoulders to hips
        (11, 12),             # Hips
        (11, 13), (13, 15),    # Left leg (hip -> knee -> ankle)
        (12, 14), (14, 16)     # Right leg (hip -> knee -> ankle)
    ]

    abs_kpts = []
    # Compute absolute coordinates and draw keypoint circles.
    for kp in kpts:
        y, x, conf = kp
        abs_coord = (int(x * width), int(y * height), conf)
        abs_kpts.append(abs_coord)
        if conf > threshold:
            cv2.circle(frame, (int(x * width), int(y * height)), 5, (0, 255, 0), -1)

    # Draw skeleton connections and add labels.
    for connection in skeleton_connections:
        i, j = connection
        x1, y1, conf1 = abs_kpts[i]
        x2, y2, conf2 = abs_kpts[j]
        if conf1 > threshold and conf2 > threshold:
            cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            # Compute midpoint for label.
            mid_x = int((x1 + x2) / 2)
            mid_y = int((y1 + y2) / 2)
            label = f"{JOINT_LABELS[i]} - {JOINT_LABELS[j]}"
            cv2.putText(frame, label, (mid_x, mid_y), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (255, 255, 255), 1, cv2.LINE_AA)
    return frame