import tkinter as tk
from tkinter import ttk
from db import get_users, get_events, add_event, update_event, delete_event, update_user_role
import datetime
import matplotlib.pyplot as plt
from collections import defaultdict
import subprocess
import sys

root = tk.Tk()
root.title("Admin Panel")
root.geometry("1160x727")
root.configure(bg="#1e1e2f")

root.update_idletasks()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = (screen_width // 2) - (1160 // 2)
y = (screen_height // 2) - (727 // 2)
root.geometry(f"1160x727+{x}+{y}")

style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", background="#2b2b3d", foreground="white", fieldbackground="#2b2b3d")
style.map("Treeview", background=[("selected", "#5a5aff")])
style.configure("TButton", background="#3a8edb", foreground="white", font=("Segoe UI", 10, "bold"))
style.configure("TCombobox", fieldbackground="#2b2b3d", background="#2b2b3d", foreground="white")

user_roles = {}
warning_label = tk.Label(root, text="", fg="yellow", bg="#1e1e2f", font=("Segoe UI", 10, "bold"))
warning_label.place(relx=0.5, rely=0.02, anchor="center")

def show_temp_warning(msg):
    warning_label.lift()
    warning_label.config(text=msg)
    warning_label.after(3000, lambda: warning_label.config(text=""))

def refresh_data():
    tree.delete(*tree.get_children())
    for event in get_events():
        tree.insert("", "end", iid=event[0], values=event[1:])
    refresh_user_roles()

def refresh_user_roles():
    for widget in user_frame.winfo_children():
        widget.destroy()
    users = get_users()
    global user_roles
    user_roles = {}
    row = 0
    for name, data in users.items():
        role = data['role']
        tk.Label(user_frame, text=name, fg="white", bg="#1e1e2f", font=("Segoe UI", 10)).grid(row=row, column=0, padx=(5, 10), pady=5, sticky="w")
        role_var = tk.StringVar(value=role)
        user_roles[name] = role_var
        role_menu = ttk.Combobox(user_frame, values=["admin", "user"], textvariable=role_var, width=12)
        role_menu.grid(row=row, column=1, padx=(10, 5), pady=5, sticky="e")
        row += 1
    update_btn = tk.Button(user_frame, text="Update All", bg="#3a8edb", fg="white", command=update_all_roles)
    update_btn.grid(row=row, column=0, columnspan=2, pady=(15, 5))
    user_frame.grid_columnconfigure(0, weight=1)
    user_frame.grid_columnconfigure(1, weight=1)

def update_all_roles():
    for name, role_var in user_roles.items():
        update_user_role(name, role_var.get())
    refresh_user_roles()
    show_temp_warning("All roles updated successfully")

def open_log_editor(initial_values=None):
    log_window = tk.Toplevel(root)
    log_window.title("Log Editor")
    log_window.configure(bg="#1e1e2f")
    root.update_idletasks()
    w, h = 270, 190
    x = root.winfo_x() + (root.winfo_width() // 2) - (w // 2)
    y = root.winfo_y() + (root.winfo_height() // 2) - (h // 2)
    log_window.geometry(f"{w}x{h}+{x}+{y}")
    log_window.grab_set()
    labels = ["Driver", "Date", "Time", "Event"]
    entries = []
    
    for i, label in enumerate(labels):
        tk.Label(log_window, text=label, fg="white", bg="#1e1e2f", font=("Segoe UI", 10, "bold")).grid(row=i, column=0, padx=(20, 5), pady=5, sticky="e")
        entry = tk.Entry(log_window, width=28)
        if initial_values:
            entry.insert(0, initial_values[i])
        entry.grid(row=i, column=1, padx=(5, 20), pady=5, sticky="w")
        entries.append(entry)
    def save():
        driver, date_str, time_str, event = [e.get().strip() for e in entries]
        if driver not in get_users():
            show_temp_warning("Driver name not found.")
            return
        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
            datetime.datetime.strptime(time_str, "%H:%M:%S")
        except ValueError:
            show_temp_warning("Invalid date or time format.")
            return
        if initial_values:
            update_event(tree.focus(), driver, date_str, time_str, event)
        else:
            add_event(driver, date_str, time_str, event)
        log_window.destroy()
        refresh_data()
    tk.Button(log_window, text="Save", bg="#3a8edb", fg="white", font=("Segoe UI", 10, "bold"), width=20, command=save).grid(row=5, column=0, columnspan=2, pady=15)

def add_log(): open_log_editor()
def edit_log():
    selected = tree.focus()
    if not selected:
        show_temp_warning("Select a log to edit")
        return
    values = tree.item(selected, "values")
    open_log_editor(values)

def delete_log():
    selected = tree.focus()
    if not selected:
        show_temp_warning("Select a log to delete")
        return
    delete_event(selected)
    refresh_data()

def show_statistic(option, metric):
    events = get_events()
    if not events:
        show_temp_warning("No logs to display statistics")
        return
    trip_counts = defaultdict(int)
    fatigue_counts = defaultdict(int)
    durations = defaultdict(int)
    last_start = {}
    for _, driver, date, time, event in events:
        dt = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S")
        if event == "start_trip":
            last_start[driver] = dt
            trip_counts[driver] += 1
        elif event == "fatigue_detected":
            fatigue_counts[driver] += 1
        elif event == "stop_trip" and driver in last_start:
            durations[driver] += int((dt - last_start[driver]).total_seconds()) // 60
            del last_start[driver]
    drivers = trip_counts.keys() if option == "All" else [option]
    fig, ax = plt.subplots()
    if metric == "Trips":
        data = {d: trip_counts.get(d, 0) for d in drivers}
        ax.set_title("Trips per Driver")
    elif metric == "Fatigue":
        data = {d: fatigue_counts.get(d, 0) for d in drivers}
        ax.set_title("Fatigue Events per Driver")
    elif metric == "Duration":
        data = {d: durations.get(d, 0) for d in drivers}
        ax.set_title("Total Drive Duration (min)")
    ax.bar(data.keys(), data.values(), color="skyblue")
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    plt.show()

def go_back_to_main():
    root.destroy()
    subprocess.run([sys.executable, "main.py"])

main_frame = tk.Frame(root, bg="#1e1e2f")
main_frame.pack(fill="both", expand=True, padx=20, pady=(50, 10))

content_frame = tk.Frame(main_frame, bg="#1e1e2f")
content_frame.pack(fill="both", expand=True)
content_frame.grid_rowconfigure(0, weight=1)
content_frame.grid_columnconfigure(0, weight=2)
content_frame.grid_columnconfigure(1, weight=1)

log_frame = tk.LabelFrame(content_frame, text="Event Logs", bg="#1e1e2f", fg="white", font=("Segoe UI", 11, "bold"))
log_frame.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=10, pady=10)

columns = ("Driver", "Date", "Time", "Event")
tree = ttk.Treeview(log_frame, columns=columns, show="headings")
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor="center")
tree.pack(fill="both", expand=True)

btn_frame = tk.Frame(log_frame, bg="#1e1e2f")
btn_frame.pack(pady=10)
tk.Button(btn_frame, text="Add Log", command=add_log, bg="#3a8edb", fg="white").pack(side="left", padx=5)
tk.Button(btn_frame, text="Edit Log", command=edit_log, bg="#3a8edb", fg="white").pack(side="left", padx=5)
tk.Button(btn_frame, text="Delete Log", command=delete_log, bg="#3a8edb", fg="white").pack(side="left", padx=5)

right_frame = tk.Frame(content_frame, bg="#1e1e2f")
right_frame.grid(row=0, column=1, rowspan=3, sticky="nsew", pady=10)
right_frame.grid_rowconfigure(0, weight=1)
right_frame.grid_rowconfigure(1, weight=1)
right_frame.grid_rowconfigure(2, weight=1)

user_frame = tk.LabelFrame(right_frame, text="Users & Roles", bg="#1e1e2f", fg="white", font=("Segoe UI", 11, "bold"))
user_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=(0, 10))

stats_frame = tk.LabelFrame(right_frame, text="Statistics", bg="#1e1e2f", fg="white", font=("Segoe UI", 11, "bold"))
stats_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 10))

tk.Label(stats_frame, text="Select Driver", bg="#1e1e2f", fg="white").pack()
driver_options = ["All"] + list(get_users().keys())
driver_var = tk.StringVar(value="All")
ttk.Combobox(stats_frame, values=driver_options, textvariable=driver_var, width=15).pack(pady=5)

tk.Button(stats_frame, text="Trips", bg="#5a5aff", fg="white", width=20, command=lambda: show_statistic(driver_var.get(), "Trips")).pack(pady=3)
tk.Button(stats_frame, text="Fatigue", bg="#5a5aff", fg="white", width=20, command=lambda: show_statistic(driver_var.get(), "Fatigue")).pack(pady=3)
tk.Button(stats_frame, text="Duration", bg="#5a5aff", fg="white", width=20, command=lambda: show_statistic(driver_var.get(), "Duration")).pack(pady=3)

filters_frame = tk.LabelFrame(right_frame, text="Filters", bg="#1e1e2f", fg="white", font=("Segoe UI", 11, "bold"))
filters_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=(0, 10))

tk.Label(filters_frame, text="Driver", bg="#1e1e2f", fg="white").grid(row=0, column=0, sticky="w", padx=5, pady=5)
filter_driver_var = tk.StringVar(value="All")
ttk.Combobox(filters_frame, values=["All"] + list(get_users().keys()), textvariable=filter_driver_var, width=15).grid(row=0, column=1, padx=5, pady=5)

tk.Label(filters_frame, text="Event", bg="#1e1e2f", fg="white").grid(row=1, column=0, sticky="w", padx=5, pady=5)
filter_event_var = tk.StringVar(value="All")
ttk.Combobox(filters_frame, values=["All", "start_trip", "fatigue_detected", "stop_trip", "short_break", "long_break"], textvariable=filter_event_var, width=15).grid(row=1, column=1, padx=5, pady=5)

def apply_filter():
    tree.delete(*tree.get_children())
    selected_driver = filter_driver_var.get()
    selected_event = filter_event_var.get()

    for event in get_events():
        _, driver, date, time, ev_type = event
        match_driver = (selected_driver == "All") or (driver == selected_driver)
        match_event = (
            (selected_event == "All") or
            (selected_event in ev_type if selected_event in ["short_break", "long_break"] else ev_type == selected_event)
        )
        if match_driver and match_event:
            tree.insert("", "end", iid=event[0], values=event[1:])

def reset_filter():
    filter_driver_var.set("All")
    filter_event_var.set("All")
    refresh_data()

btn_frame_filters = tk.Frame(filters_frame, bg="#1e1e2f")
btn_frame_filters.grid(row=2, column=0, columnspan=2, pady=10)
tk.Button(btn_frame_filters, text="Apply Filter", bg="#3a8edb", fg="white", command=apply_filter).pack(side="left", padx=5)
tk.Button(btn_frame_filters, text="Reset", bg="#777", fg="white", command=reset_filter).pack(side="left", padx=5)

bottom_frame = tk.Frame(root, bg="#1e1e2f")
bottom_frame.pack(fill="x")
tk.Button(bottom_frame, text="← Back to Main", bg="#444", fg="white", command=go_back_to_main).pack(side="left", padx=20, pady=10)
tk.Button(bottom_frame, text="Exit", bg="red", fg="white", command=root.destroy).pack(side="right", padx=20, pady=10)

refresh_data()
root.mainloop()
