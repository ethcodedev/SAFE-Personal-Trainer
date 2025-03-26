import numpy as np
import math

def evaluate_squat(keypoints, squat_reps, previousAngle, current_pos):
    feedback = []
    depthFeedback, new_count, new_prevAngle, new_curr_pos = are_knees_bending(keypoints,squat_reps,previousAngle,current_pos)
    backResults = is_back_straight(keypoints)
    headResults = is_head_up(keypoints)

    feedback.append(depthFeedback)
    feedback.append(backResults)
    feedback.append(headResults)

    return feedback, new_count, new_prevAngle, new_curr_pos
def get_bending_angle(top: np.ndarray, middle: np.ndarray, bottom: np.ndarray) -> float:
   
    # Femur (thigh)
    vector1 = (middle[0] - top[0], middle[1] - top[1])
    # Tibia (shin)
    vector2 = (bottom[0] - middle[0], bottom[1] - middle[1])

    # Compute dot product
    dot_product = vector1[0] * vector2[0] + vector1[1] * vector2[1]

    # Compute magnitudes
    magnitude1 = math.sqrt(vector1[0]**2 + vector1[1]**2)
    magnitude2 = math.sqrt(vector2[0]**2 + vector2[1]**2)

    # Avoid division by zero
    if magnitude1 == 0 or magnitude2 == 0:
        return 0

    # Calculate angle in radians
    cosine_theta = np.clip(dot_product / (magnitude1 * magnitude2), -1.0, 1.0)
    angle_radians = math.acos(cosine_theta)

    # Convert to degrees
    angle_degrees = math.degrees(angle_radians)

    return angle_degrees

def get_back_angle(hip: np.ndarray, shoulder: np.ndarray) -> float:
    """Calculate the angle of the back relative to the vertical y-axis.

    Args:
        hip (np.ndarray): (x, y, confidence) of the hip keypoint.
        shoulder (np.ndarray): (x, y, confidence) of the shoulder keypoint.


    """
    # Vector from hip to shoulder (back direction)
    vector1 = (shoulder[0] - hip[0], shoulder[1] - hip[1])
    #if (hip[0] > shoulder[0]):
     #   vector2 = (0, 1)
    #else:
    vector2 = (0, -1)
    

    # Compute dot product
    dot_product = vector1[0] * vector2[0] + vector1[1] * vector2[1]

    # Compute magnitude of vector1
    magnitude1 = math.sqrt(vector1[0]**2 + vector1[1]**2)

    # Avoid division by zero
    if magnitude1 == 0:
        return 0

    # Calculate angle in radians
    cosine_theta = np.clip(dot_product / magnitude1, -1.0, 1.0)
    angle_radians = math.acos(cosine_theta)

    # Convert to degrees
    angle_degrees = math.degrees(angle_radians)

    return angle_degrees


def are_knees_bending(kps: np.ndarray, squat_reps:int,previousAngle:float,current_pos:str):
    """Check if the knees are bending based on MoveNet keypoints.

    Args:
        kps (np.ndarray): Array of (x, y, confidence) for all 17 MoveNet keypoints.

    Returns:
        bool: True if knees are bending (angle > 50 degrees), otherwise False.
    """
    feedback = "Evaluating depth..."
    # MoveNet keypoint indices (from the MoveNet model)
    RIGHT_HIP = 12
    RIGHT_KNEE = 14
    RIGHT_ANKLE = 16
    LEFT_HIP = 11
    LEFT_KNEE = 13
    LEFT_ANKLE = 15

    right_hip = kps[RIGHT_HIP]
    right_knee = kps[RIGHT_KNEE]
    right_ankle = kps[RIGHT_ANKLE]

    left_hip = kps[LEFT_HIP]
    left_knee = kps[LEFT_KNEE]
    left_ankle = kps[LEFT_ANKLE]

    right_leg_angle = get_bending_angle(right_hip, right_knee, right_ankle)
    left_leg_angle = get_bending_angle(left_hip, left_knee, left_ankle)
    avg_angle = (left_leg_angle + right_leg_angle) / 2
    if avg_angle > 30 and previousAngle < 30 and current_pos =="up":
        current_pos = "squatting"
    
    if avg_angle < previousAngle and current_pos == "squatting":
        
        current_pos = "up"
        squat_reps +=1
        
        if previousAngle < 50:
            feedback = "Bend knees all the way to 90 degrees"
        if previousAngle >= 50:
            feedback = "Good depth!"
    previousAngle = avg_angle   
    return feedback, squat_reps,previousAngle,current_pos
def is_back_straight(kps):
    feedback =""
    RIGHT_HIP = 12
    RIGHT_SHOULDER = 6
    LEFT_HIP = 11
    LEFT_SHOULDER = 5

    right_hip = kps[RIGHT_HIP]
    right_shoulder = kps[RIGHT_SHOULDER]
    left_hip = kps[LEFT_HIP]
    left_shoulder = kps[LEFT_SHOULDER]

    right_back_angle = get_back_angle(right_hip, right_shoulder)
    left_back_angle = get_back_angle(left_hip, left_shoulder)

    avg_back_angle = (right_back_angle + left_back_angle) / 2
    if avg_back_angle > 145:  # Example threshold for bending too far forward
        feedback = "Warning: Back is bent too far forward!"
    else:
        feedback = "Back is straight"
    #print(avg_back_angle)
    return feedback

def is_head_up(kps: np.ndarray):
    """Check if the user's head is up based on the angle between the nose, shoulder, and hip.

    Args:
        kps (np.ndarray): Array of (x, y, confidence) for all 17 MoveNet keypoints.

    Returns:
        bool: True if the head is up, False if the user is looking down.
    """
    NOSE = 0
    LEFT_SHOULDER = 5
    RIGHT_SHOULDER = 6
    LEFT_HIP = 11
    RIGHT_HIP = 12

    nose = kps[NOSE]
    left_shoulder = kps[LEFT_SHOULDER]
    right_shoulder = kps[RIGHT_SHOULDER]
    left_hip = kps[LEFT_HIP]
    right_hip = kps[RIGHT_HIP]
    
    # Average left and right to get a centered body position
    avg_shoulder = (left_shoulder + right_shoulder) / 2
    avg_hip = (left_hip + right_hip) / 2

    head_angle = get_bending_angle(nose, avg_shoulder, avg_hip)

    if head_angle > 60:  # Threshold for looking down (adjustable)
        feedback = "Warning: Keep your head up!"
          # User is looking down
    else:
        feedback = "Eyes are looking forward"

    return feedback