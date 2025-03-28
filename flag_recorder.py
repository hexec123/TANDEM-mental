import tkinter as tk
from tkinter import filedialog
import csv
import time
import os

class FlagRecorderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Flag Recorder App")

        self.filepath = None
        self.flag_count = 0

        self.create_widgets()

        # Bind window closing event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        self.file_button = tk.Button(self.root, text="Select File", command=self.select_file)
        self.file_button.grid(row=0, column=0, columnspan=2)

        self.file_label = tk.Label(self.root, text="File: ")
        self.file_label.grid(row=1, column=0, columnspan=2)

        self.flag_button = tk.Button(self.root, text="Record Flag", command=self.record_flag, height=5, width=20)
        self.flag_button.grid(row=2, column=0)

        self.flag_count_label = tk.Label(self.root, text="Flag Count: 0")
        self.flag_count_label.grid(row=2, column=1)

        self.textbox_label = tk.Label(self.root, text="Textbox:")
        self.textbox_label.grid(row=3, column=0)
        self.textbox = tk.Entry(self.root)
        self.textbox.grid(row=3, column=1)

    def select_file(self):
        self.filepath = filedialog.asksaveasfilename(initialdir='./data', defaultextension='.csv', filetypes=[('CSV files', '*.csv'), ('All files', '*.*')])
        timestamp = time.strftime('_flag_%Y%m%d_%H%M%S')
        self.flag_count = 0
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


    def record_flag(self):
        if not self.filepath:
            timestamp = time.strftime('_flag_%Y%m%d_%H%M%S')
            self.filepath = f'./data/test{timestamp}.csv'  # Add timestamp and .csv extension
        self.file_label.config(text=f"File: {os.path.basename(self.filepath)}")  # Display only the filename
        # if not self.filepath:
        #     self.filepath = './data/test'
        # if not os.path.exists(self.filepath):
        #     timestamp = time.strftime('_flag_%Y%m%d_%H%M%S')
        #     base, ext = os.path.splitext(self.filepath)
        #     self.filepath = base + timestamp + ext
        #     open(self.filepath, 'w').close()
        # self.file_label.config(text=f"File: {self.filepath}")

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.flag_count += 1
        textbox_content = self.textbox.get()
        with open(self.filepath, "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([timestamp, self.flag_count, textbox_content])

        self.flag_count_label.config(text=f"Flag Count: {self.flag_count}")

    def on_closing(self):
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = FlagRecorderApp(root)
    root.mainloop()
