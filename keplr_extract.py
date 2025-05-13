import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import os
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

class KeplrExtractApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Keplr EEG Extractor & Plotter")
        self.file_path = None
        self.eeg_path = None
        self.processed_path = None
        self.plot_window_eeg = None
        self.plot_window_processed = None
        self.selected_columns = []

        self.select_button = tk.Button(root, text="Select CSV File", command=self.select_file)
        self.select_button.pack(pady=10)

        self.convert_button = tk.Button(root, text="Convert EEG (_keplr) & Processed (_keplr_processed)", command=self.convert, state=tk.DISABLED)
        self.convert_button.pack(pady=5)

        self.plot_eeg_button = tk.Button(root, text="View EEG Plot", command=self.plot_eeg, state=tk.DISABLED)
        self.plot_eeg_button.pack(pady=5)

        self.plot_processed_button = tk.Button(root, text="View Processed Plot", command=self.plot_processed, state=tk.DISABLED)
        self.plot_processed_button.pack(pady=5)

        self.status_label = tk.Label(root, text="No file selected.")
        self.status_label.pack(pady=10)

    def select_file(self):
        file_path = filedialog.askopenfilename(title="Select CSV file", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not file_path:
            return
        self.file_path = file_path
        self.eeg_path = os.path.splitext(file_path)[0] + '_keplr.csv'
        self.processed_path = os.path.splitext(file_path)[0] + '_keplr_processed.csv'
        self.status_label.config(text=f"Selected: {os.path.basename(file_path)}")
        self.convert_button.config(state=tk.NORMAL)
        self.plot_eeg_button.config(state=tk.NORMAL if os.path.exists(self.eeg_path) else tk.DISABLED)
        self.plot_processed_button.config(state=tk.NORMAL if os.path.exists(self.processed_path) else tk.DISABLED)

    def convert(self):
        if not self.file_path:
            messagebox.showerror("Error", "No file selected.")
            return
        df = pd.read_csv(self.file_path, sep=';', low_memory=False)
        # EEG extraction
        eeg_raw_cols = [col for col in df.columns if col.startswith('Bio_EEG_RAW')]
        if 'Bio_Time' not in df.columns or not eeg_raw_cols:
            messagebox.showerror("Error", "Required EEG columns not found.")
            return
        # Only keep Bio_Time and EEG_RAW* columns for EEG extraction
        eeg_cols = ['Bio_Time'] + eeg_raw_cols
        df_eeg = df[eeg_cols].drop_duplicates(subset=eeg_cols)
        df_eeg = df_eeg.sort_values('Bio_Time')
        eeg_output = []
        sample_rate = 1024.0
        # Parse Bio_Time as seconds since start
        def parse_time_to_seconds(t):
            import re
            if pd.isnull(t):
                return None
            if isinstance(t, (int, float)):
                return float(t)
            t = str(t).strip()
            # Try to parse hh:mm:ss(.ms) or mm:ss(.ms) or ss(.ms)
            parts = re.split(r'[:]', t)
            try:
                parts = [float(p) for p in parts]
            except Exception:
                return None
            if len(parts) == 3:
                return parts[0]*3600 + parts[1]*60 + parts[2]
            elif len(parts) == 2:
                return parts[0]*60 + parts[1]
            elif len(parts) == 1:
                return parts[0]
            return None
        # Compute offset so time starts at zero
        times = df_eeg['Bio_Time'].map(parse_time_to_seconds)
        if times.isnull().all():
            messagebox.showerror("Error", "Could not parse any Bio_Time values. Check the time format.")
            return
        time_offset = times.dropna().iloc[0] if not times.dropna().empty else 0.0
        for idx, row in df_eeg.iterrows():
            base_ts = parse_time_to_seconds(row['Bio_Time'])
            if base_ts is None:
                continue
            base_ts -= time_offset
            for i, col in enumerate(eeg_raw_cols):
                ts = base_ts + i / sample_rate
                val = row[col]
                if pd.notnull(val):
                    eeg_output.append((ts, val))
        eeg_output = sorted(set(eeg_output), key=lambda x: x[0])
        with open(self.eeg_path, 'w') as f:
            f.write('timestamp,value\n')
            for ts, val in eeg_output:
                f.write(f'{ts},{val}\n')
        # Processed extraction
        processed_cols = ['Bio_Time', 'Bio_Focus', 'Bio_Agitation', 'Bio_Delta', 'Bio_Theta', 'Bio_Beta', 'Bio_Alpha', 'Bio_Gamma']
        missing = [col for col in processed_cols if col not in df.columns]
        if missing:
            messagebox.showerror("Error", f"Missing processed columns: {', '.join(missing)}")
            return
        df_proc = df[processed_cols].drop_duplicates(subset=['Bio_Time']).sort_values('Bio_Time').copy()
        # Convert Bio_Time to seconds since start for processed features
        proc_times = df_proc['Bio_Time'].map(parse_time_to_seconds)
        proc_offset = proc_times.dropna().iloc[0] if not proc_times.dropna().empty else 0.0
        df_proc['Bio_Time'] = proc_times - proc_offset
        df_proc.to_csv(self.processed_path, index=False)
        self.status_label.config(text=f'Converted: {os.path.basename(self.eeg_path)}, {os.path.basename(self.processed_path)}')
        self.plot_eeg_button.config(state=tk.NORMAL)
        self.plot_processed_button.config(state=tk.NORMAL)

    def plot_eeg(self):
        if not self.eeg_path or not os.path.exists(self.eeg_path):
            messagebox.showerror("Error", "EEG file not found.")
            return
        df = pd.read_csv(self.eeg_path)
        if self.plot_window_eeg is not None and tk.Toplevel.winfo_exists(self.plot_window_eeg):
            self.plot_window_eeg.lift()
            return
        self.plot_window_eeg = tk.Toplevel(self.root)
        self.plot_window_eeg.title("EEG Plot - Seaborn/Matplotlib")
        fig, ax = plt.subplots(figsize=(10, 4))
        sns.lineplot(x=df['timestamp'], y=df['value'], ax=ax)
        ax.set_title("EEG Signal")
        ax.set_xlabel("Timestamp (s)")
        ax.set_ylabel("EEG Value")
        canvas = FigureCanvasTkAgg(fig, master=self.plot_window_eeg)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        toolbar = NavigationToolbar2Tk(canvas, self.plot_window_eeg)
        toolbar.update()
        canvas._tkcanvas.pack(fill="both", expand=True)

    def plot_processed(self):
        if not self.processed_path or not os.path.exists(self.processed_path):
            messagebox.showerror("Error", "Processed file not found.")
            return
        df = pd.read_csv(self.processed_path)
        if self.plot_window_processed is not None and tk.Toplevel.winfo_exists(self.plot_window_processed):
            self.plot_window_processed.lift()
            return
        self.plot_window_processed = tk.Toplevel(self.root)
        self.plot_window_processed.title("Processed Plot - Seaborn/Matplotlib")
        # Column selection
        col_frame = tk.Frame(self.plot_window_processed)
        col_frame.pack(side="top", fill="x")
        var_dict = {}
        def update_plot(*_):
            selected = [col for col, var in var_dict.items() if var.get()]
            ax.clear()
            for col in selected:
                ax.plot(df['Bio_Time'], df[col], label=col)
            ax.set_title("Processed EEG Features")
            ax.set_xlabel("Bio_Time (s)")
            ax.set_ylabel("Value")
            ax.legend()
            canvas.draw()
        fig, ax = plt.subplots(figsize=(10, 4))
        for i, col in enumerate(df.columns):
            if col == 'Bio_Time':
                continue
            var = tk.BooleanVar(value=True)
            var_dict[col] = var
            cb = tk.Checkbutton(col_frame, text=col, variable=var, command=update_plot)
            cb.pack(side="left")
        canvas = FigureCanvasTkAgg(fig, master=self.plot_window_processed)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        toolbar = NavigationToolbar2Tk(canvas, self.plot_window_processed)
        toolbar.update()
        canvas._tkcanvas.pack(fill="both", expand=True)
        update_plot()

if __name__ == "__main__":
    root = tk.Tk()
    app = KeplrExtractApp(root)
    root.mainloop()
