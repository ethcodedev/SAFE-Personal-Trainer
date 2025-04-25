import cv2
from PIL import Image, ImageTk

class WebcamHandler:
    def __init__(self, source=0):
        self.capture = cv2.VideoCapture(source)
        self.writer = None
        self.recording = False
        self.video_path = None
        self.frame_size = (
            int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        )

    def start_recording(self, output_path):
        self.video_path = output_path
        self.writer = cv2.VideoWriter(
            output_path,
            cv2.VideoWriter_fourcc(*"XVID"),
            20.0,
            self.frame_size
        )
        self.recording = True

    def get_frame(self):
        ret, frame = self.capture.read()
        if not ret:
            return None
        if self.recording and self.writer:
            self.writer.write(frame)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return ImageTk.PhotoImage(image=Image.fromarray(rgb_frame))

    def stop_recording(self):
        self.recording = False
        if self.writer:
            self.writer.release()
            self.writer = None

    def release(self):
        self.stop_recording()
        self.capture.release()
