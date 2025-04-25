import tkinter as tk
from tkinter import ttk, messagebox
import time
import threading
import os
from datetime import datetime
from webcam import WebcamHandler
from tkVideoPlayer import TkinterVideo


# Mock data
def get_rep_count():
    return 12

def get_heart_rate():
    return 82

PRIMARY_BG = "#1e1e1e"
ACCENT_BG = "#2c3e50"
BUTTON_BG = "#c0392b"
BUTTON_HOVER_BG = "#e74c3c"
TEXT_COLOR = "#ecf0f1"
ENTRY_BG = "#34495e"

class StyledButton(ttk.Button):
    _style_count = 0
    def __init__(self, master=None, **kwargs):
        style = ttk.Style(master)
        style.theme_use("clam")
        style_name = f"Custom.TButton{StyledButton._style_count}"
        StyledButton._style_count += 1
        style.layout(style_name, style.layout("TButton"))
        style.configure(style_name, background=BUTTON_BG, foreground=TEXT_COLOR,
                        font=("Helvetica", 18), padding=10, borderwidth=0)
        style.map(style_name, background=[("pressed", BUTTON_HOVER_BG), ("active", BUTTON_HOVER_BG)],
                  foreground=[("pressed", TEXT_COLOR), ("active", TEXT_COLOR)])
        kwargs["style"] = style_name
        super().__init__(master, **kwargs)

class StyledEntry(tk.Entry):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.default_text = ""
        self.configure(bg=ENTRY_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR,
                       font=("Helvetica", 16), relief="flat",
                       highlightthickness=2, highlightbackground=BUTTON_BG)
        self.bind("<FocusIn>", self.on_focus_in)
        self.bind("<FocusOut>", self.on_focus_out)

    def set_default(self, text):
        self.default_text = text
        self.delete(0, tk.END)
        self.insert(0, text)
        self.configure(fg="#888888")

    def on_focus_in(self, event):
        if self.get() == self.default_text:
            self.delete(0, tk.END)
            self.configure(fg=TEXT_COLOR)

    def on_focus_out(self, event):
        if not self.get():
            self.insert(0, self.default_text)
            self.configure(fg="#888888")

class WorkoutApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Workout Tracker")
        self.root.configure(bg=PRIMARY_BG)
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)

        self.webcam = WebcamHandler()
        self.workout_running = False
        self.workout_type = tk.StringVar(value="Push Ups")
        self.minutes = tk.IntVar(value=0)
        self.seconds = tk.IntVar(value=30)

        self.init_prompt()

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def init_prompt(self):
        self.clear_screen()
        frame = tk.Frame(self.root, bg=PRIMARY_BG)
        frame.pack(expand=True, fill="both")
        StyledButton(frame, text="Start New Workout", command=self.new_workout_screen).pack(pady=20)
        StyledButton(frame,  text="View Previous Workouts", command=self.view_previous_workouts).pack(pady=20)

    def view_previous_workouts(self):
        self.clear_screen()
        StyledButton(self.root, text="Back", command=self.init_prompt).pack(anchor='nw', padx=20, pady=20)
        tk.Label(self.root, text="Previous Workouts:", fg=TEXT_COLOR, bg=PRIMARY_BG, font=("Helvetica", 24)).pack(
            pady=10)

        scroll_frame = tk.Frame(self.root, bg=PRIMARY_BG)
        scroll_frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(scroll_frame, bg=PRIMARY_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=PRIMARY_BG)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        if not os.path.exists("prev_workout"):
            os.makedirs("prev_workout")

        folders = sorted(os.listdir("prev_workout"))
        if not folders:
            tk.Label(scrollable_frame, text="No workouts yet – go get those gains!",
                     fg=TEXT_COLOR, bg=PRIMARY_BG, font=("Helvetica", 18)).pack(pady=20)
        else:
            for folder in reversed(folders):
                folder_path = os.path.join("prev_workout", folder)
                if os.path.isdir(folder_path):
                    text_file = os.path.join(folder_path, "workout_data.txt")
                    if os.path.exists(text_file):
                        with open(text_file, "r") as f:
                            content = f.read()
                        tk.Label(scrollable_frame, text=content, fg=TEXT_COLOR, bg=PRIMARY_BG,
                                 font=("Helvetica", 16), wraplength=800, justify="left").pack(pady=10, anchor="w")

                    # 🔽 Add video preview if any video file exists in the folder
                    video_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.mp4', '.avi', '.mov'))]
                    if video_files:
                        video_path = os.path.join(folder_path, video_files[0])
                        if os.path.exists(video_path):
                            tk.Label(scrollable_frame, text="Video Preview:", fg=TEXT_COLOR, bg=PRIMARY_BG,
                                     font=("Helvetica", 16)).pack(anchor="w", padx=20)
                            player = TkinterVideo(scrollable_frame, scaled=True, pre_load=False)
                            player.load(video_path)
                            player.pack(padx=20, pady=10, anchor="w")
                            player.play()

    def new_workout_screen(self):
        self.clear_screen()
        tk.Label(self.root, text="Select Workout Type", fg=TEXT_COLOR, bg=PRIMARY_BG, font=("Helvetica", 24)).pack(pady=10)
        workout_menu = ttk.Combobox(self.root, textvariable=self.workout_type,
                                    values=["Push Ups", "Sit Ups", "Squats", "Jumping Jacks"], font=("Helvetica", 18))
        workout_menu.pack(pady=10)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", fieldbackground=ACCENT_BG, background=ACCENT_BG, foreground=TEXT_COLOR)

        tk.Label(self.root, text="Set Duration:", fg=TEXT_COLOR, bg=PRIMARY_BG, font=("Helvetica", 24)).pack(pady=10)
        time_frame = tk.Frame(self.root, bg=PRIMARY_BG)
        time_frame.pack(pady=5)

        tk.Label(time_frame, text="Minutes", fg=TEXT_COLOR, bg=PRIMARY_BG, font=("Helvetica", 16)).grid(row=0, column=0, padx=10)
        tk.Label(time_frame, text="Seconds", fg=TEXT_COLOR, bg=PRIMARY_BG, font=("Helvetica", 16)).grid(row=0, column=1, padx=10)

        tk.Spinbox(time_frame, from_=0, to=59, textvariable=self.minutes, font=("Helvetica", 18), width=5,
                   bg=ACCENT_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR).grid(row=1, column=0, padx=10)
        tk.Spinbox(time_frame, from_=0, to=59, textvariable=self.seconds, font=("Helvetica", 18), width=5,
                   bg=ACCENT_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR).grid(row=1, column=1, padx=10)

        StyledButton(self.root, text="Start Workout", command=self.pre_countdown).pack(pady=20)

    def pre_countdown(self):
        self.clear_screen()
        countdown_label = tk.Label(self.root, text="", font=("Helvetica", 72), fg=TEXT_COLOR, bg=PRIMARY_BG)
        countdown_label.pack(expand=True, fill="both")

        def do_countdown():
            for i in range(3, 0, -1):
                countdown_label.config(text=str(i))
                self.root.update()
                time.sleep(1)
            self.start_workout()

        threading.Thread(target=do_countdown).start()

    def toggle_pause(self):
        self.paused = not self.paused
        self.pause_btn.config(text="Resume" if self.paused else "Pause")

    def start_workout(self):
        self.time_remaining = tk.IntVar(value=self.minutes.get() * 60 + self.seconds.get())
        self.clear_screen()

        # Generate temporary path for video recording
        video_filename = f"{self.workout_type.get()}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.avi"
        self.video_output_path = os.path.join("prev_workout", video_filename)
        self.webcam.start_recording(self.video_output_path)

        self.workout_running = True

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        self.video_frame = tk.Label(self.root, bg=PRIMARY_BG)
        self.video_frame.grid(row=0, column=0, rowspan=5, sticky="nsew", padx=10, pady=10)

        self.right_frame = tk.Frame(self.root, bg=PRIMARY_BG)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.type_label = tk.Label(self.right_frame, text=f"Workout: {self.workout_type.get()}",
                                   fg=TEXT_COLOR, bg=PRIMARY_BG, font=("Helvetica", 20))
        self.type_label.pack(pady=10)

        self.time_label = tk.Label(self.right_frame, text="", fg=TEXT_COLOR, bg=PRIMARY_BG, font=("Helvetica", 20))
        self.time_label.pack(pady=10)

        self.rep_label = tk.Label(self.right_frame, text="Reps: --", font=("Helvetica", 32), fg=TEXT_COLOR, bg=PRIMARY_BG)
        self.rep_label.pack(pady=40)

        self.hr_label = tk.Label(self.right_frame, text="Heart Rate: -- bpm", font=("Helvetica", 24), fg=TEXT_COLOR, bg=PRIMARY_BG)
        self.hr_label.pack(pady=20)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.right_frame, variable=self.progress_var,
                                            maximum=self.time_remaining.get(), length=300)
        self.progress_bar.pack(pady=10)

        control_frame = tk.Frame(self.right_frame, bg=PRIMARY_BG)
        control_frame.pack(side="bottom", pady=30)

        self.pause_btn = StyledButton(control_frame, text="Pause", command=self.toggle_pause)
        self.pause_btn.grid(row=0, column=0, padx=10)

        StyledButton(control_frame, text="End Workout", command=self.end_workout).grid(row=0, column=1, padx=10)

        self.paused = False
        self.update_video()
        self.update_workout_timer()
        self.update_data()

    def update_video(self):
        if not self.workout_running:
            return
        frame = self.webcam.get_frame()
        if frame:
            self.video_frame.imgtk = frame
            self.video_frame.configure(image=frame)
        self.root.after(10, self.update_video)

    def update_workout_timer(self):
        if self.workout_running and not self.paused:
            current = self.time_remaining.get()
            if current > 0:
                self.time_remaining.set(current - 1)
                mins, secs = divmod(self.time_remaining.get(), 60)
                self.time_label.config(text=f"Time Left: {mins:02}:{secs:02}")
                self.progress_var.set(self.progress_var.get() + 1)
                if current <= 5:
                    self.time_label.config(fg=BUTTON_HOVER_BG)
                self.root.after(1000, self.update_workout_timer)
            else:
                self.end_workout()
        elif self.workout_running:
            self.root.after(500, self.update_workout_timer)

    def update_data(self):
        if not self.workout_running:
            return
        self.rep_label.config(text=f"Reps: {get_rep_count()}")
        self.hr_label.config(text=f"Heart Rate: {get_heart_rate()} bpm")
        self.root.after(1000, self.update_data)

    def end_workout(self):
        self.workout_running = False
        self.webcam.stop_recording()

        workout_name = f"{self.workout_type.get()} {datetime.now().strftime('%Y-%m-%d %H-%M-%S')}"
        folder_path = os.path.join("prev_workout", workout_name)
        os.makedirs(folder_path, exist_ok=True)

        if hasattr(self, "video_output_path") and os.path.exists(self.video_output_path):
            final_video_path = os.path.join(folder_path, os.path.basename(self.video_output_path))
            os.rename(self.video_output_path, final_video_path)

        self.webcam.release()
        self.clear_screen()

        wrapper = tk.Frame(self.root, bg=PRIMARY_BG)
        wrapper.pack(expand=True, fill="both", padx=20, pady=20)

        tk.Label(wrapper, text="Name Your Workout", fg=TEXT_COLOR, bg=PRIMARY_BG, font=("Helvetica", 24)).pack(pady=20)

        name_var = tk.StringVar()
        entry = StyledEntry(wrapper, textvariable=name_var)
        entry.set_default(workout_name)
        entry.pack(pady=10, ipadx=10, ipady=5, fill="x", expand=True)

        def save_and_exit():
            name = name_var.get().strip() or workout_name
            final_folder = os.path.join("prev_workout", name)
            os.rename(folder_path, final_folder)
            file_path = os.path.join(final_folder, "workout_data.txt")
            with open(file_path, "w") as f:
                f.write(
                    f"Workout: {self.workout_type.get()}\n"
                    f"Name: {name}\n"
                    f"Duration: {self.minutes.get() * 60 + self.seconds.get()}s\n"
                    f"Reps: {get_rep_count()}\n"
                    f"Heart Rate: {get_heart_rate()} bpm\n"
                )
            messagebox.showinfo("Workout Saved", "Workout successfully saved.")
            self.init_prompt()

        StyledButton(wrapper, text="Save Workout", command=save_and_exit).pack(pady=20)

if __name__ == "__main__":
    root = tk.Tk()
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)
    app = WorkoutApp(root)
    root.mainloop()
