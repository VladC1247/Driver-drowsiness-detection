import argparse
import cv2
import pygame
import tkinter as tk
from datetime import datetime
from PIL import Image, ImageTk
from ultralytics import YOLO
from db import log_event, init_db

parser = argparse.ArgumentParser()
parser.add_argument("--weights", type=str, default="yolov8.pt")
parser.add_argument("--device", type=str, default="cpu")
parser.add_argument("--conf-thres", type=float, default=0.25)
parser.add_argument("--user", type=str, default="unknown")
opt = parser.parse_args()

init_db()
log_event(opt.user, "start_trip")
pygame.mixer.init()
pygame.mixer.music.load("alarm.wav")
model = YOLO(opt.weights)
cap = cv2.VideoCapture(0)

fatigue_level = 0
fatigue_max = 100
alarm_on = False
fatigue_logged = False

mode = "drive"
start_time = datetime.now()
pause_start = None
short_break_logged = False
long_break_logged = False

def show_temp_popup(message, duration=2500, bg="#007acc", fg="white"):
    popup = tk.Toplevel()
    popup.overrideredirect(True)
    popup.configure(bg="#2c2f3a", padx=10, pady=5, highlightthickness=1, highlightbackground="#555")
    label = tk.Label(popup, text=message, font=("Segoe UI", 12, "bold"), bg=bg, fg=fg, padx=20, pady=10)
    label.pack()
    popup.update_idletasks()
    width = popup.winfo_width()
    height = popup.winfo_height()
    x = popup.winfo_screenwidth() // 2 - width // 2
    y = popup.winfo_screenheight() // 2 - height // 2
    popup.geometry(f"{width}x{height}+{x}+{y}")
    popup.after(duration, popup.destroy)

window = tk.Tk()
window.title("Driver Drowsiness Detection")
window.geometry("960x640")
window.configure(bg="#1e1e2f")  # dark background

video_frame = tk.Label(window, bg="#2c2f3a", bd=2, relief="ridge", highlightbackground="#444", highlightthickness=1)
video_frame.pack(pady=10)

info_frame = tk.Frame(window, bg="#1e1e2f")
info_frame.pack()

timer_label = tk.Label(info_frame, text="", font=("Segoe UI", 16, "bold"), bg="#1e1e2f", fg="#e0e0e0")
timer_label.pack()

btn_frame = tk.Frame(window, bg="#1e1e2f")
btn_frame.pack(pady=10)

btn_style = {
    "font": ("Segoe UI", 12),
    "width": 18,
    "height": 2,
    "bg": "#3498db",
    "fg": "white",
    "activebackground": "#2980b9",
    "bd": 0
}

stop_btn_style = btn_style.copy()
stop_btn_style.update({"bg": "#d9534f", "activebackground": "#c9302c"})

btn_short = tk.Button(btn_frame, text="Start Short Break", **btn_style)
btn_short.grid(row=0, column=0, padx=10)

btn_long = tk.Button(btn_frame, text="Start Long Break", **btn_style)
btn_long.grid(row=0, column=1, padx=10)

btn_stop = tk.Button(btn_frame, text="Stop Trip", **stop_btn_style)
btn_stop.grid(row=0, column=2, padx=10)

def stop_trip():
    log_event(opt.user, "stop_trip")
    if cap and cap.isOpened():
        cap.release()
    pygame.mixer.music.stop()
    window.quit()
    window.destroy()

def on_close():
    stop_trip()

window.protocol("WM_DELETE_WINDOW", on_close)

def update_timer_label():
    elapsed = datetime.now() - (start_time if mode == "drive" else pause_start)
    mins, secs = divmod(int(elapsed.total_seconds()), 60)
    color = {"drive": "lightgreen", "short_break": "orange", "long_break": "skyblue"}[mode]
    label = {"drive": "Drive Time", "short_break": "Short Break", "long_break": "Long Break"}[mode]
    timer_label.config(text=f"{label}: {mins:02}:{secs:02}", fg=color)

def toggle_short_break():
    global mode, pause_start, short_break_logged
    if mode == "drive":
        mode = "short_break"
        pause_start = datetime.now()
        btn_short.config(text="Stop Short Break")
    elif mode == "short_break":
        mode = "drive"
        btn_short.config(text="Start Short Break")
        short_break_logged = False

def toggle_long_break():
    global mode, pause_start, long_break_logged, start_time
    if mode == "drive":
        mode = "long_break"
        pause_start = datetime.now()
        log_event(opt.user, "start_long_break")
        btn_long.config(text="Stop Long Break")
    elif mode == "long_break":
        elapsed = (datetime.now() - pause_start).total_seconds()
        if elapsed < 45:
            log_event(opt.user, "early_long_break_stopped")
        log_event(opt.user, "stop_long_break")
        mode = "drive"
        btn_long.config(text="Start Long Break")
        long_break_logged = False
        start_time = datetime.now()

btn_short.config(command=toggle_short_break)
btn_long.config(command=toggle_long_break)
btn_stop.config(command=stop_trip)

def update_frame():
    global fatigue_level, fatigue_logged, alarm_on, short_break_logged, long_break_logged

    ret, frame = cap.read()
    if not ret:
        window.after(10, update_frame)
        return

    update_timer_label()

    if mode == "short_break":
        elapsed = (datetime.now() - pause_start).total_seconds()
        if elapsed > 10 and not short_break_logged:
            log_event(opt.user, "short_break_exceeded")
            short_break_logged = True
        cv2.putText(frame, "Short Break Active", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 140, 255), 3)

    elif mode == "long_break":
        elapsed = (datetime.now() - pause_start).total_seconds()
        if elapsed > 60 and not long_break_logged:
            log_event(opt.user, "long_break_exceeded")
            long_break_logged = True
        cv2.putText(frame, "Long Break Active", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)

    elif mode == "drive":
        if (datetime.now() - start_time).total_seconds() > 240:
            log_event(opt.user, "drive_overtime")

        results = model.predict(source=frame, conf=opt.conf_thres, device=opt.device, verbose=False)
        detected_labels = set()

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls)
                label = model.names[cls_id]
                detected_labels.add(label)

        if "awake" in detected_labels and "drowsy" in detected_labels:
            detected_labels.remove("awake")

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls)
                label = model.names[cls_id]
                if label not in detected_labels:
                    continue
                xyxy = box.xyxy[0].cpu().numpy().astype(int)
                conf = float(box.conf[0])
                color = (255, 0, 0) if label == "awake" else (0, 0, 255)
                cv2.rectangle(frame, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), color, 2)
                cv2.putText(frame, f"{label.upper()} {conf:.2f}", (xyxy[0], xyxy[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

                if label == 'drowsy':
                    fatigue_level = min(fatigue_max, fatigue_level + 1)
                elif label == 'awake':
                    fatigue_level = max(0, fatigue_level - 1)

        ratio = fatigue_level / fatigue_max
        filled_w = int(ratio * frame.shape[1])
        cv2.rectangle(frame, (0, 0), (frame.shape[1], 25), (230, 230, 230), -1)
        cv2.rectangle(frame, (0, 0), (filled_w, 25), (0, 0, 255), -1)

        if ratio > 0.75:
            cv2.putText(frame, "DROWSY ALERT!", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
            if not alarm_on:
                pygame.mixer.music.play(-1)
                alarm_on = True
            if not fatigue_logged:
                log_event(opt.user, "fatigue_detected")
                fatigue_logged = True
        else:
            if alarm_on:
                pygame.mixer.music.stop()
                alarm_on = False
            if fatigue_level < 0.5 * fatigue_max:
                fatigue_logged = False

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img_tk = ImageTk.PhotoImage(Image.fromarray(rgb))
    video_frame.imgtk = img_tk
    video_frame.configure(image=img_tk)
    window.after(10, update_frame)

update_frame()
window.mainloop()
