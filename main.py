import cv2
import tkinter as tk
from tkinter import simpledialog
from PIL import Image, ImageTk
import subprocess
import threading
import time
import face_recognition
import numpy as np
from db import init_db, get_users, get_user, add_user

def show_temp_popup(message, duration=2500, bg="#007acc", fg="white"):
    popup = tk.Toplevel()
    popup.overrideredirect(True)
    popup.configure(bg="#2c2f3a", padx=10, pady=5, highlightthickness=1, highlightbackground="#555")
    label = tk.Label(popup, text=message, font=("Segoe UI", 12, "bold"), bg=bg, fg=fg, padx=20, pady=10, bd=0)
    label.pack()


    popup.update_idletasks()
    width = popup.winfo_width()
    height = popup.winfo_height()
    x = popup.winfo_screenwidth() // 2 - width // 2
    y = popup.winfo_screenheight() // 2 - height // 2
    popup.geometry(f"{width}x{height}+{x}+{y}")
    popup.after(duration, popup.destroy)

def prompt_new_username():
    popup = tk.Tk()
    popup.withdraw()
    name = simpledialog.askstring("New User", "Enter your name:")
    popup.destroy()
    return name

def get_embedding(image):
    face_locations = face_recognition.face_locations(image)
    if face_locations:
        return face_recognition.face_encodings(image, known_face_locations=face_locations)[0].tolist()
    return None

def recognize_person(embedding, database, tolerance=0.5):
    for name, data in database.items():
        match = face_recognition.compare_faces([np.array(data["embedding"])], np.array(embedding), tolerance=tolerance)
        if match[0]:
            return name
    return None

def is_admin(name):
    user = get_user(name)
    return user and user.get("role") == "admin"

def capture_and_process(frame):
    db = get_users()
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    embedding = get_embedding(rgb_frame)
    if embedding:
        person = recognize_person(embedding, db)
        if person:
            print(f"Recognized person: {person}", flush=True)
            return person, True
        else:
            name = prompt_new_username()
            if name:
                add_user(name, embedding)
                print(f"New user added: {name}")
                return name, True
            else:
                print("User cancelled name entry.")
                return "unknown", False
    print("No face detected.")
    return "unknown", False

def start_detection_after_delay(person_name):
    time.sleep(1.2)
    subprocess.run(["python", "drowsiness_detection.py", "--user", person_name])

def on_start_click(root, cap):
    ret, frame = cap.read()
    if ret:
        person_name, success = capture_and_process(frame)
        if person_name == "unknown" or not success:
            show_temp_popup("Face not detected or user not confirmed.\nPlease try again.", bg="#f39c12")
            return
        cap.release()
        root.quit()
        root.destroy()
        threading.Thread(target=start_detection_after_delay, args=(person_name,)).start()

def on_admin_click(root, cap):
    ret, frame = cap.read()
    if ret:
        person_name, success = capture_and_process(frame)
        if success and is_admin(person_name):
            cap.release()
            root.quit()
            root.destroy()
            subprocess.run(["python", "admin_panel.py", "--user", person_name])
        else:
            show_temp_popup("You do not have administrator privileges.", bg="#d9534f")

def center_window(window, width=960, height=640):
    screen_w = window.winfo_screenwidth()
    screen_h = window.winfo_screenheight()
    x = int((screen_w - width) / 2)
    y = int((screen_h - height) / 2)
    window.geometry(f"{width}x{height}+{x}+{y}")

def show_start_gui():
    init_db()
    root = tk.Tk()
    root.title("Driver Drowsiness Detection")
    center_window(root)
    root.configure(bg="#1e1e2f")

    video_frame = tk.Label(root, bg="#2c2f3a", bd=2, relief="ridge", highlightbackground="#444", highlightthickness=1)
    video_frame.pack(pady=20)

    cap = cv2.VideoCapture(0)

    def update_frame():
        ret, frame = cap.read()
        if ret:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_frame)
            imgtk = ImageTk.PhotoImage(image=img)
            video_frame.imgtk = imgtk
            video_frame.configure(image=imgtk)
        root.after(20, update_frame)

    def on_close():
        cap.release()
        root.quit()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    update_frame()

    button_frame = tk.Frame(root, bg="#1e1e2f")
    button_frame.pack(pady=10)

    btn_style = {"font": ("Segoe UI", 14),"width": 18,"bg": "#3498db","fg": "white","activebackground": "#2980b9","bd": 0,"height": 2}
    
    exit_btn_style = {"font": ("Segoe UI", 14),"width": 18,"bg": "#d9534f","fg": "white","activebackground": "#c9302c","bd": 0,"height": 2}

    start_btn = tk.Button(button_frame, text="Start Trip", command=lambda: on_start_click(root, cap), **btn_style)
    start_btn.grid(row=0, column=0, padx=15)

    admin_btn = tk.Button(button_frame, text="Admin Panel", command=lambda: on_admin_click(root, cap), **btn_style)
    admin_btn.grid(row=0, column=1, padx=15)
    
    exit_btn = tk.Button(button_frame, text="Exit", command=lambda: on_close(), **exit_btn_style)
    exit_btn.grid(row=0, column=2, padx=15)

    root.mainloop()

if __name__ == "__main__":
    try:
        show_start_gui()
    except Exception as e:
        print(f"[ERROR] {e}")
