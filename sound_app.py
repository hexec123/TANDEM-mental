import tkinter as tk
from tkinter import filedialog
import csv
import time
import threading
import os
import numpy as np
import pygame
import json

class SoundApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sound Player App")

        self.filepath = None
        self.is_running = False
        self.count1 = 0
        self.count2 = 0
        self.thread1 = None
        self.thread2 = None

        self.config_file = './config.json'
        self.config = self.load_config()

        self.create_widgets()
        self.sample_rate = 44100
        pygame.mixer.init()

        # Bind window closing event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {"freq1": 440, "freq2": 880, "interval1": 2, "interval2": 3}

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)

    def create_widgets(self):
        tk.Label(self.root, text="Frequency 1 (Hz):").grid(row=0, column=0)
        self.freq1_entry = tk.Entry(self.root)
        self.freq1_entry.grid(row=0, column=1)
        self.freq1_entry.insert(0, self.config.get("freq1", 440))
        self.freq1_entry.bind("<KeyRelease>", self.update_config)

        tk.Label(self.root, text="Interval 1 (s):").grid(row=0, column=2)
        self.interval1_entry = tk.Entry(self.root)
        self.interval1_entry.grid(row=0, column=3)
        self.interval1_entry.insert(0, self.config.get("interval1", 1))
        self.interval1_entry.bind("<KeyRelease>", self.update_config)

        tk.Label(self.root, text="Frequency 2 (Hz):").grid(row=1, column=0)
        self.freq2_entry = tk.Entry(self.root)
        self.freq2_entry.grid(row=1, column=1)
        self.freq2_entry.insert(0, self.config.get("freq2", 880))
        self.freq2_entry.bind("<KeyRelease>", self.update_config)

        tk.Label(self.root, text="Interval 2 (s):").grid(row=1, column=2)
        self.interval2_entry = tk.Entry(self.root)
        self.interval2_entry.grid(row=1, column=3)
        self.interval2_entry.insert(0, self.config.get("interval2", 1))
        self.interval2_entry.bind("<KeyRelease>", self.update_config)

        self.freq1_count_label = tk.Label(self.root, text="Count: 0")
        self.freq1_count_label.grid(row=0, column=4)

        self.freq2_count_label = tk.Label(self.root, text="Count: 0")
        self.freq2_count_label.grid(row=1, column=4)

        self.file_button = tk.Button(self.root, text="Select File", command=self.select_file)
        self.file_button.grid(row=2, column=0, columnspan=4)

        self.file_label = tk.Label(self.root, text="File: ")
        self.file_label.grid(row=3, column=0, columnspan=4)

        self.start_button = tk.Button(self.root, text="Start", command=self.start)
        self.start_button.grid(row=4, column=0, columnspan=2)

        self.stop_button = tk.Button(self.root, text="Stop", command=self.stop)
        self.stop_button.grid(row=4, column=2, columnspan=2)

    def update_config(self, event):
        try:
            self.config["freq1"] = float(self.freq1_entry.get())
            self.config["freq2"] = float(self.freq2_entry.get())
            self.config["interval1"] = float(self.interval1_entry.get())
            self.config["interval2"] = float(self.interval2_entry.get())
            self.save_config()
        except ValueError:
            pass

    def select_file(self):
        self.filepath = filedialog.asksaveasfilename(initialdir='./data', defaultextension='.csv', filetypes=[('CSV files', '*.csv'), ('All files', '*.*')])
        timestamp = time.strftime('_sound_%Y%m%d_%H%M%S')
        if not self.filepath:
            self.filepath = f'./data/test{timestamp}.csv'  # Add timestamp and .csv extension
        else:
            base, ext = os.path.splitext(self.filepath)
            if ext.lower() != '.csv':
                self.filepath = base + timestamp + '.csv'  # Ensure timestamp and .csv extension
            elif timestamp not in base:  # Avoid appending timestamp if already present
                self.filepath = base + timestamp + ext
        if not os.path.exists(self.filepath):
            open(self.filepath, 'w').close()
        self.file_label.config(text=f"File: {os.path.basename(self.filepath)}")  # Display only the filename
        # self.count1 = 0  # Reset count when a new file is selected
        # self.count2 = 0  # Reset count when a new file is selected

    def start(self):
        if not self.filepath:
            timestamp = time.strftime('_sound_%Y%m%d_%H%M%S')
            self.filepath = f'./data/test{timestamp}.csv'  # Add timestamp and .csv extension
        self.file_label.config(text=f"File: {os.path.basename(self.filepath)}")  # Display only the filename
        try:
            self.freq1 = float(self.freq1_entry.get())
            self.freq2 = float(self.freq2_entry.get())
            self.interval1 = float(self.interval1_entry.get())
            self.interval2 = float(self.interval2_entry.get())
        except ValueError:
            tk.messagebox.showerror("Error", "Please enter valid frequencies and intervals.")
            return

        self.is_running = True
        self.count1 = 1  # Start count at 1
        self.count2 = 1  # Start count at 1
        self.thread1 = threading.Thread(target=self.play_sound, args=(1, self.freq1, self.interval1, 0))
        self.thread2 = threading.Thread(target=self.play_sound, args=(2, self.freq2, self.interval2, 0.5))  # Offset by the duration of the first sound
        self.thread1.start()
        self.thread2.start()

    def stop(self):
        self.is_running = False
        self.thread1.join()
        self.thread2.join()
        # self.root.quit()  # Commented out to prevent app shutdown

    def play_sound(self, sound_number, frequency, interval, initial_offset=0):
        time.sleep(initial_offset)  # Offset the start time of the sound
        while self.is_running:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            self.record_to_csv(timestamp, sound_number)
            if sound_number == 1:
                self.freq1_count_label.config(text=f"Count: {self.count1}")
                print(f"Sound {sound_number} played at {timestamp} - Count: {self.count1}")
                self.count1 += 1
            else:
                self.freq2_count_label.config(text=f"Count: {self.count2}")
                print(f"Sound {sound_number} played at {timestamp} - Count: {self.count2}")
                self.count2 += 1
            self.generate_sound(frequency, 0.5)  # Generate sound at the specified frequency for 0.5 seconds
            time.sleep(interval - 0.5)  # Adjust sleep time to account for sound duration

    def generate_sound(self, freq, duration):
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        buf = np.zeros((n_samples, 2), dtype=np.int16)
        max_sample = 2**15 - 1
        for s in range(n_samples):
            t = float(s) / sample_rate
            buf[s][0] = int(max_sample * 0.5 * np.sin(2.0 * np.pi * freq * t))  # Left channel
            buf[s][1] = int(max_sample * 0.5 * np.sin(2.0 * np.pi * freq * t))  # Right channel
        sound = pygame.sndarray.make_sound(buf)
        sound.play()
        pygame.time.delay(int(duration * 1000))
        sound.stop()

    def record_to_csv(self, timestamp, sound_number):
        with open(self.filepath, "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            if sound_number == 1:
                writer.writerow([timestamp, sound_number, self.count1])
            else:
                writer.writerow([timestamp, sound_number, self.count2])

    def on_closing(self):
        self.is_running = False
        if self.thread1 and self.thread1.is_alive():
            self.thread1.join()
        if self.thread2 and self.thread2.is_alive():
            self.thread2.join()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SoundApp(root)
    root.mainloop()
