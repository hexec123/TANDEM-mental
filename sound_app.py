import tkinter as tk
from tkinter import filedialog
import csv
import time
import threading

class SoundApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sound Player App")

        self.filepath = None
        self.is_running = False

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="Frequency 1 (seconds):").grid(row=0, column=0)
        self.freq1_entry = tk.Entry(self.root)
        self.freq1_entry.grid(row=0, column=1)

        tk.Label(self.root, text="Frequency 2 (seconds):").grid(row=1, column=0)
        self.freq2_entry = tk.Entry(self.root)
        self.freq2_entry.grid(row=1, column=1)

        self.file_button = tk.Button(self.root, text="Select File", command=self.select_file)
        self.file_button.grid(row=2, column=0, columnspan=2)

        self.start_button = tk.Button(self.root, text="Start", command=self.start)
        self.start_button.grid(row=3, column=0)

        self.stop_button = tk.Button(self.root, text="Stop", command=self.stop)
        self.stop_button.grid(row=3, column=1)

    def select_file(self):
        self.filepath = filedialog.askopenfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])

    def start(self):
        if not self.filepath:
            tk.messagebox.showerror("Error", "Please select a file first.")
            return

        try:
            self.freq1 = float(self.freq1_entry.get())
            self.freq2 = float(self.freq2_entry.get())
        except ValueError:
            tk.messagebox.showerror("Error", "Please enter valid frequencies.")
            return

        self.is_running = True
        self.thread1 = threading.Thread(target=self.play_sound, args=(1, self.freq1))
        self.thread2 = threading.Thread(target=self.play_sound, args=(2, self.freq2))
        self.thread1.start()
        self.thread2.start()

    def stop(self):
        self.is_running = False
        self.thread1.join()
        self.thread2.join()

    def play_sound(self, sound_number, frequency):
        while self.is_running:
            time.sleep(frequency)
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            self.record_to_csv(timestamp, sound_number)
            print(f"Sound {sound_number} played at {timestamp}")

    def record_to_csv(self, timestamp, sound_number):
        with open(self.filepath, "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([timestamp, sound_number])

if __name__ == "__main__":
    root = tk.Tk()
    app = SoundApp(root)
    root.mainloop()
