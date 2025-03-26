import cv2
import tensorflow as tf
import numpy as np
import tensorflow_hub as hub
import kagglehub as kh
import math

def compute_pushup_angles(keypoints, frame_shape):
    """
    Compute angles required for analyzing push-up form:
      - The angle between the left and right shoulders.
      - The angle at the right elbow.
      - The body alignment angle (right shoulder to right hip relative to horizontal).
      - The ratio of the right elbow's horizontal offset from the body's midline.
    """
    height, width, _ = frame_shape
    kpts = keypoints[0, 0, :, :]  # Shape: (17, 3)

    def to_abs(kp):
        y, x, conf = kp
        return (int(x * width), int(y * height), conf)

    # Shoulders for level check.
    left_shoulder = to_abs(kpts[5])
    right_shoulder = to_abs(kpts[6])
    dx_shoulder = right_shoulder[0] - left_shoulder[0]
    dy_shoulder = right_shoulder[1] - left_shoulder[1]
    angle_shoulder = abs(math.degrees(math.atan2(dy_shoulder, dx_shoulder)))
    
    # Compute the right elbow angle.
    def calculate_angle(a, b, c):
        ba = np.array([a[0] - b[0], a[1] - b[1]])
        bc = np.array([c[0] - b[0], c[1] - b[1]])
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
        cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
        return math.degrees(np.arccos(cosine_angle))
    
    right_elbow = to_abs(kpts[8])
    right_wrist = to_abs(kpts[10])
    right_shoulder_point = (right_shoulder[0], right_shoulder[1])
    right_elbow_point = (right_elbow[0], right_elbow[1])
    right_wrist_point = (right_wrist[0], right_wrist[1])
    angle_elbow = calculate_angle(right_shoulder_point, right_elbow_point, right_wrist_point)
    
    # Compute body alignment: angle between right shoulder and right hip.
    right_hip = to_abs(kpts[12])
    dx_body = right_hip[0] - right_shoulder[0]
    dy_body = right_hip[1] - right_shoulder[1]
    angle_body_alignment = abs(math.degrees(math.atan2(dy_body, dx_body)))
    
    # Compute elbow offset from the body's midline.
    left_hip = to_abs(kpts[11])
    mid_shoulder_x = (left_shoulder[0] + right_shoulder[0]) / 2
    mid_hip_x = (left_hip[0] + right_hip[0]) / 2
    midline_x = (mid_shoulder_x + mid_hip_x) / 2
    elbow_offset = abs(right_elbow[0] - midline_x)
    dist_shoulder_hip = math.sqrt((right_hip[0] - right_shoulder[0])**2 + (right_hip[1] - right_shoulder[1])**2)
    elbow_offset_ratio = elbow_offset / (dist_shoulder_hip + 1e-6)
    
    angles = {
        "left_shoulderright_shoulder": angle_shoulder,
        "right_shoulderright_elbow": angle_elbow,
        "body_alignment": angle_body_alignment,
        "elbow_offset_ratio": elbow_offset_ratio
    }
    return angles

def analyze_pushup_form(angles, criteria):
    """
    Given computed angles and the push-up criteria, evaluate the form and return feedback messages.
    """
    feedback = []
    for criterion in criteria:
        if criterion["condition"](angles):
            feedback.append(criterion["feedback_pass"])
        else:
            feedback.append(criterion["feedback_fail"])
    return feedback


