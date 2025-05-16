import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tkinter import Tk, filedialog
from scipy.signal import find_peaks

# --- Config ---
SAMPLING_RATE = 130  # Hz
WINDOW_SECONDS = 5
WINDOW_SAMPLES = int(WINDOW_SECONDS * SAMPLING_RATE)

# --- Select file with Tkinter ---
root = Tk()
root.withdraw()
file_path = filedialog.askopenfilename(title="Select ECG CSV File", filetypes=[("CSV Files", "*.csv")])
if not file_path:
    raise Exception("No file selected")

# --- Load ECG data ---
df = pd.read_csv(file_path)

# Assume 'value' column holds the ECG data
signal = df['value'].values

# --- Detect R-peaks ---
# Normalize the signal
norm_signal = (signal - np.mean(signal)) / np.std(signal)

# Find peaks (tweak height and distance if needed)
peaks, _ = find_peaks(norm_signal, distance=30, height=0.5)

# Convert peak indices to timestamps (in seconds)
peak_times = np.array(peaks) / SAMPLING_RATE

# --- Plot raw EEG signal with detected peaks ---
import matplotlib.widgets as mwidgets

# Time axis for the signal
time_axis = np.arange(len(signal)) / SAMPLING_RATE

# Initial window (20 seconds)
window_sec = 20
window_samples = int(window_sec * SAMPLING_RATE)
start_idx = 0
end_idx = start_idx + window_samples

fig, ax = plt.subplots(figsize=(12, 5))
line_signal, = ax.plot(time_axis[start_idx:end_idx], signal[start_idx:end_idx], label='Raw EEG Signal')
peak_mask = (peaks >= start_idx) & (peaks < end_idx)
peak_plot = ax.plot(time_axis[peaks[peak_mask]], signal[peaks[peak_mask]], 'ro', label='Detected Peaks')
ax.set_xlabel('Time (s)')
ax.set_ylabel('EEG Value')
ax.set_title('Raw EEG Signal with Detected Peaks')
ax.legend()
ax.grid(True)

# Add scroll bar (slider) for navigation
from matplotlib.widgets import Slider
axcolor = 'lightgoldenrodyellow'
ax_slider = plt.axes([0.15, 0.01, 0.7, 0.03], facecolor=axcolor)
slider = Slider(ax_slider, 'Start Time (s)', 0, max(time_axis) - window_sec, valinit=0, valstep=1)

def update(val):
    global peak_plot  # Declare global variable at the start
    start = int(slider.val * SAMPLING_RATE)
    end = start + window_samples
    line_signal.set_xdata(time_axis[start:end])
    line_signal.set_ydata(signal[start:end])
    # Update peaks
    peak_mask = (peaks >= start) & (peaks < end)
    # Remove old peak plot and plot new
    for l in peak_plot:
        l.remove()
    new_peaks = ax.plot(time_axis[peaks[peak_mask]], signal[peaks[peak_mask]], 'ro', label='Detected Peaks')
    # Keep reference to new peak plot
    peak_plot = new_peaks
    ax.set_xlim(time_axis[start], time_axis[min(end, len(signal)-1)])
    fig.canvas.draw_idle()

slider.on_changed(update)

# Enable zoom and pan
plt.tight_layout(rect=[0, 0.04, 1, 1])
plt.show()
