import tkinter as tk
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import csv
import os
import time
import threading
import sys

# Dynamically add the Polar_Lib directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
polar_lib_path = os.path.join(current_dir, '../cta_das_library/Polar_Lib')
sys.path.append(os.path.normpath(polar_lib_path))

from PolarLib import DeviceH10

class ECGApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ECG Live Plot")

        self.device = None
        self.filepath = None
        self.is_running = False
        self.ecg_data = []
        self.ecg_timestamps = []
        self.n_seconds = 10
        self.battery_level = tk.StringVar(value="Battery: N/A")
        self.current_hr = tk.StringVar(value="HR: N/A")
        self.error_message = tk.StringVar(value="")

        self.create_widgets()
        self.create_plot()

    def create_widgets(self):
        # Adjust the layout to make the top section centered and less cramped
        self.top_frame = tk.Frame(self.root, height=150, width=400)
        self.top_frame.grid(row=0, column=0, sticky="n")
        self.top_frame.grid_propagate(False)
        self.top_frame.pack_propagate(False)

        self.plot_frame = tk.Frame(self.root)
        self.plot_frame.grid(row=1, column=0, sticky="nsew")

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        tk.Label(self.top_frame, text="Last N seconds:").grid(row=0, column=0)
        self.n_seconds_entry = tk.Entry(self.top_frame)
        self.n_seconds_entry.insert(0, "10")
        self.n_seconds_entry.grid(row=0, column=1, pady=5)

        self.file_button = tk.Button(self.top_frame, text="Select File", command=self.select_file)
        self.file_button.grid(row=1, column=0, columnspan=2, pady=5)

        self.start_button = tk.Button(self.top_frame, text="Start", command=self.start)
        self.start_button.grid(row=2, column=0, pady=5)

        self.stop_button = tk.Button(self.top_frame, text="Stop", command=self.stop)
        self.stop_button.grid(row=2, column=1, pady=5)

        self.filename_label = tk.Label(self.top_frame, text="No file selected", anchor="center")
        self.filename_label.grid(row=3, column=0, columnspan=2, pady=5)

        tk.Label(self.top_frame, textvariable=self.battery_level).grid(row=4, column=0, columnspan=2)
        tk.Label(self.top_frame, textvariable=self.current_hr).grid(row=5, column=0, columnspan=2)
        tk.Label(self.top_frame, textvariable=self.error_message, fg="red").grid(row=6, column=0, columnspan=2)

    def create_plot(self):
        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot([], [], lw=2)
        self.ax.set_xlim(0, self.n_seconds)
        self.ax.set_ylim(-500, 500)
        self.ax.set_title("ECG Live Plot")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("ECG Value")

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def select_file(self):
        self.filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not os.path.exists(self.filepath):
            timestamp = time.strftime("_%Y%m%d_%H%M%S")
            base, ext = os.path.splitext(self.filepath)
            self.filepath = base + timestamp + ext
        self.filename_label.config(text=os.path.basename(self.filepath))

    def start(self):
        if not self.filepath:
            timestamp = time.strftime("_%Y%m%d_%H%M%S")
            self.filepath = f"./data/ecg_raw_{timestamp}.csv"

        self.is_running = True
        self.error_message.set("")  # Clear any previous error messages

        try:
            self.device = DeviceH10("MAC_ADDRESS", debug_mode=False)
            self.device.received_data_cb = self.process_data

            self.thread = threading.Thread(target=self.device.connect_async)
            self.thread.start()

            self.ani = FuncAnimation(self.fig, self.update_plot, interval=1000)
        except Exception as e:
            self.is_running = False
            self.error_message.set(f"Error: {str(e)}")
            self.root.after(100, lambda: None)  # Force the GUI to refresh

    def stop(self):
        self.is_running = False
        if self.device:
            self.device.stop()
        if hasattr(self, 'thread') and self.thread.is_alive():
            self.thread.join(timeout=1)  # Ensure the thread stops within a timeout

        self.device = None  # Explicitly set the device to None to release resources

        # Stop the animation if it exists
        if hasattr(self, 'ani') and self.ani:
            self.ani.event_source.stop()
            self.ani = None

    def process_data(self, device):
        if not self.is_running:
            return

        self.ecg_data.extend(device.last_ecg_values)
        self.ecg_timestamps.extend(device.ecg_stream_times)

        with open(self.filepath, "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            for timestamp, value in zip(device.ecg_stream_times, device.last_ecg_values):
                writer.writerow([timestamp, value])

        self.battery_level.set(f"Battery: {device.battery_level}%")
        self.current_hr.set(f"HR: {device.last_hr_value}")

    def update_plot(self, frame):
        try:
            self.n_seconds = int(self.n_seconds_entry.get())
        except ValueError:
            self.n_seconds = 10

        current_time = time.time()
        filtered_data = [(t, v) for t, v in zip(self.ecg_timestamps, self.ecg_data) if current_time - t <= self.n_seconds]

        if filtered_data:
            times, values = zip(*filtered_data)
            self.line.set_data(times, values)
            self.ax.set_xlim(min(times), max(times))
            self.ax.set_ylim(min(values), max(values))

        self.canvas.draw()
        return self.line,

    def on_closing(self):
        self.stop()  # Ensure the script stops when the window is closed
        self.root.destroy()

# Update the main block to bind the on_closing method to the window close event
if __name__ == "__main__":
    root = tk.Tk()
    app = ECGApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)  # Bind the close event
    root.mainloop()