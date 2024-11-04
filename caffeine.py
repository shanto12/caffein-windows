import tkinter as tk
from tkinter import ttk
from datetime import datetime, time, timedelta
import json
import threading
import ctypes
import win32api
import win32con
import time as t
import sys
import os
from pathlib import Path

class CaffeineApp:
    def __init__(self):
        self.settings_file = Path('caffeine_settings.json')
        self.running = True
        self.active = False
        self.next_window = None
        self.current_window_end = None
        self.status_lock = threading.Lock()  # Add lock for thread safety
        
        print(f"[{self.get_timestamp()}] Starting Caffeine service...")
        
        if self.settings_file.exists():
            print(f"[{self.get_timestamp()}] Loading saved settings...")
            self.load_settings()
            self.run_background()
        else:
            print(f"[{self.get_timestamp()}] First run detected. Opening setup window...")
            self.show_setup_gui()

    def get_timestamp(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def load_settings(self):
        with open(self.settings_file, 'r') as f:
            self.settings = json.load(f)

    def save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def show_setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Caffeine Setup")
        self.root.geometry("500x400")

        main_frame = ttk.Frame(self.root)
        main_frame.pack(padx=20, pady=10, fill="both", expand=True)

        ttk.Label(main_frame, text="Configure Active Hours", font=('', 12, 'bold')).pack(pady=(0, 10))

        days_frame = ttk.Frame(main_frame)
        days_frame.pack(fill="both", expand=True)

        self.day_vars = []
        self.time_entries = []
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        # Create headers
        ttk.Label(days_frame, text="Day", width=10).grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(days_frame, text="Active", width=8).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(days_frame, text="Start Time", width=10).grid(row=0, column=2, padx=5, pady=5)
        ttk.Label(days_frame, text="End Time", width=10).grid(row=0, column=3, padx=5, pady=5)

        for i, day in enumerate(days):
            # Day label
            ttk.Label(days_frame, text=day).grid(row=i+1, column=0, padx=5, pady=5)
            
            # Active checkbox
            var = tk.BooleanVar(value=True)
            self.day_vars.append(var)
            ttk.Checkbutton(days_frame, variable=var).grid(row=i+1, column=1, padx=5, pady=5)
            
            # Time entries frame
            time_frame = ttk.Frame(days_frame)
            time_frame.grid(row=i+1, column=2, columnspan=2, pady=5)
            
            # Start time
            start_hour = ttk.Spinbox(time_frame, from_=0, to=23, width=3, format="%02.0f")
            start_hour.set("09")
            start_min = ttk.Spinbox(time_frame, from_=0, to=59, width=3, format="%02.0f")
            start_min.set("00")
            
            # End time
            end_hour = ttk.Spinbox(time_frame, from_=0, to=23, width=3, format="%02.0f")
            end_hour.set("17")
            end_min = ttk.Spinbox(time_frame, from_=0, to=59, width=3, format="%02.0f")
            end_min.set("00")
            
            start_hour.pack(side="left", padx=2)
            ttk.Label(time_frame, text=":").pack(side="left")
            start_min.pack(side="left", padx=2)
            
            ttk.Label(time_frame, text="-").pack(side="left", padx=5)
            
            end_hour.pack(side="left", padx=2)
            ttk.Label(time_frame, text=":").pack(side="left")
            end_min.pack(side="left", padx=2)
            
            self.time_entries.append((start_hour, start_min, end_hour, end_min))

        def save():
            settings = {'days': []}
            for i, (var, (sh, sm, eh, em)) in enumerate(zip(self.day_vars, self.time_entries)):
                if var.get():
                    settings['days'].append({
                        'day': i,
                        'start': f"{int(sh.get()):02d}:{int(sm.get()):02d}",
                        'end': f"{int(eh.get()):02d}:{int(em.get()):02d}"
                    })
            
            self.settings = settings
            self.save_settings()
            self.root.destroy()
            self.run_background()

        ttk.Button(main_frame, text="Save and Start", command=save).pack(pady=20)
        self.root.mainloop()

    def is_active_window(self):
        now = datetime.now()
        current_day = now.weekday()
        
        for day_config in self.settings['days']:
            if day_config['day'] == current_day:
                current_time = now.time()
                start = datetime.strptime(day_config['start'], '%H:%M').time()
                end = datetime.strptime(day_config['end'], '%H:%M').time()
                
                if start <= current_time <= end:
                    self.current_window_end = datetime.combine(now.date(), end)
                    return True
                
        return False

    def get_next_window(self):
        now = datetime.now()
        current_day = now.weekday()
        current_time = now.time()
        
        # Check today's window
        for day_config in self.settings['days']:
            if day_config['day'] == current_day:
                start = datetime.strptime(day_config['start'], '%H:%M').time()
                if start > current_time:
                    return datetime.combine(now.date(), start)
        
        # Check next 7 days
        for days_ahead in range(1, 8):
            next_day = (current_day + days_ahead) % 7
            for day_config in self.settings['days']:
                if day_config['day'] == next_day:
                    next_date = now.date() + timedelta(days=days_ahead)
                    start = datetime.strptime(day_config['start'], '%H:%M').time()
                    return datetime.combine(next_date, start)
        
        return None

    def prevent_sleep(self):
        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        
        while self.running:
            is_active = self.is_active_window()
            with self.status_lock:
                if is_active:
                    if not self.active:
                        self.active = True
                        self.log("Caffeine activated")
                    
                    # Prevent system sleep
                    ctypes.windll.kernel32.SetThreadExecutionState(
                        ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
                    
                    # Simulate minimal activity
                    win32api.keybd_event(win32con.VK_F15, 0, 0, 0)
                    win32api.keybd_event(win32con.VK_F15, 0, win32con.KEYEVENTF_KEYUP, 0)
                    
                else:
                    if self.active:
                        self.active = False
                        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
                        self.log("Caffeine deactivated")
                    
                    self.next_window = self.get_next_window()
            
            t.sleep(60)

    def log(self, message):
        print(f"[{self.get_timestamp()}] {message}")

    def run_background(self):
        self.log("Configuration loaded successfully")
        self.log("Active days and times:")
        for day_config in self.settings['days']:
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            self.log(f"  {day_names[day_config['day']]}: {day_config['start']} - {day_config['end']}")
        
        # Start prevention thread
        threading.Thread(target=self.prevent_sleep, daemon=True).start()
        
        # Main loop for status updates
        try:
            while True:
                with self.status_lock:
                    if self.is_active_window():  # Check current status directly
                        self.log(f"Currently active - will run until: {self.current_window_end.strftime('%H:%M')}")
                    else:
                        next_window = self.get_next_window()
                        if next_window:
                            self.log(f"Currently inactive - next activation: {next_window.strftime('%Y-%m-%d %H:%M')}")
                        else:
                            self.log("Currently inactive - no upcoming active windows scheduled")
                t.sleep(300)  # Status update every 5 minutes
        except KeyboardInterrupt:
            self.running = False
            self.log("Caffeine service stopped")
            sys.exit(0)

if __name__ == "__main__":
    CaffeineApp()