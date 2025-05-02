import cv2
from PIL import Image, ImageTk


class WebcamHandler:
    def __init__(self, source=0):
        self.source = source
        self.capture = None
        self.writer = None
        self.recording = False
        self.video_path = None
        self.frame_size = (640, 480)  # default, will update later

    def start_recording(self, output_path):
        self.capture = cv2.VideoCapture(self.source)
        if not self.capture.isOpened():
            raise RuntimeError("Cannot access webcam.")

        self.frame_size = (
            int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        )

        self.video_path = output_path
        self.writer = cv2.VideoWriter(
            output_path,
            cv2.VideoWriter_fourcc(*"XVID"),
            20.0,
            self.frame_size
        )
        self.recording = True

    def get_frame(self):
        if not self.capture:
            return None
        ret, frame = self.capture.read()
        if not ret:
            return None
        if self.recording and self.writer:
            self.writer.write(frame)
        return frame

    def stop_recording(self):
        self.recording = False
        if self.writer:
            self.writer.release()
            self.writer = None

    def release(self):
        self.stop_recording()
        if self.capture:
            self.capture.release()
            self.capture = None

