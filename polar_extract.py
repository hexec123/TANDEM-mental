# Extract ECG data from a CSV file using a Tkinter file dialog

import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import os
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class PolarExtractApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Polar ECG Extractor & Plotter")
        self.file_path = None
        self.converted_path = None

        self.select_button = tk.Button(root, text="Select CSV File", command=self.select_file)
        self.select_button.pack(pady=10)

        self.convert_button = tk.Button(root, text="Convert to _polar.csv", command=self.convert, state=tk.DISABLED)
        self.convert_button.pack(pady=5)

        self.plot_button = tk.Button(root, text="View Plot", command=self.plot, state=tk.DISABLED)
        self.plot_button.pack(pady=5)
        self.plot_window = None

        self.status_label = tk.Label(root, text="No file selected.")
        self.status_label.pack(pady=10)

    def select_file(self):
        file_path = filedialog.askopenfilename(title="Select CSV file", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not file_path:
            return
        self.file_path = file_path
        self.converted_path = os.path.splitext(file_path)[0] + '_polar.csv'
        self.status_label.config(text=f"Selected: {os.path.basename(file_path)}")
        self.convert_button.config(state=tk.NORMAL)
        if os.path.exists(self.converted_path):
            self.plot_button.config(state=tk.NORMAL)
        else:
            self.plot_button.config(state=tk.DISABLED)

    def convert(self):
        if not self.file_path:
            messagebox.showerror("Error", "No file selected.")
            return
        df = pd.read_csv(self.file_path, sep=';', low_memory=False)
        ecg_raw_cols = [col for col in df.columns if col.startswith('Bio_ECG_RAW')]
        if 'Bio_ECG_Timestamp' not in df.columns or not ecg_raw_cols:
            messagebox.showerror("Error", "Required columns not found.")
            return
        df = df.drop_duplicates(subset=['Bio_ECG_Timestamp'] + ecg_raw_cols)
        df = df.sort_values('Bio_ECG_Timestamp')
        output = []
        sample_rate = 130.0
        for _, row in df.iterrows():
            try:
                base_ts = float(row['Bio_ECG_Timestamp'])
            except Exception:
                continue
            for i, col in enumerate(ecg_raw_cols):
                ts = base_ts + i / sample_rate
                val = row[col]
                if pd.notnull(val):
                    output.append((ts, val))
        output = sorted(set(output), key=lambda x: x[0])
        with open(self.converted_path, 'w') as f:
            f.write('timestamp,value\n')
            for ts, val in output:
                f.write(f'{ts},{val}\n')
        self.status_label.config(text=f'Converted: {os.path.basename(self.converted_path)}')
        self.plot_button.config(state=tk.NORMAL)

    def plot(self):
        if not self.converted_path or not os.path.exists(self.converted_path):
            messagebox.showerror("Error", "Converted file not found.")
            return
        df = pd.read_csv(self.converted_path)
        if self.plot_window is not None and tk.Toplevel.winfo_exists(self.plot_window):
            self.plot_window.lift()
            return
        self.plot_window = tk.Toplevel(self.root)
        self.plot_window.title("ECG Plot - Seaborn/Matplotlib")
        fig, ax = plt.subplots(figsize=(10, 4))
        sns.lineplot(x=df['timestamp'], y=df['value'], ax=ax)
        ax.set_title("ECG Signal")
        ax.set_xlabel("Timestamp (s)")
        ax.set_ylabel("ECG Value")
        canvas = FigureCanvasTkAgg(fig, master=self.plot_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        # Add basic matplotlib toolbar for pan/zoom
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        toolbar = NavigationToolbar2Tk(canvas, self.plot_window)
        toolbar.update()
        canvas._tkcanvas.pack(fill="both", expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = PolarExtractApp(root)
    root.mainloop()
