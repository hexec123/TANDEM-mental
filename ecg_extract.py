import pandas as pd
from datetime import timedelta
import tkinter as tk
from tkinter import filedialog

# === File selection dialog ===
root = tk.Tk()
root.withdraw()  # Hide the main window
input_filename = filedialog.askopenfilename(title="Select CSV File", filetypes=[("CSV files", "*.csv")])
if not input_filename:
    print("No file selected. Exiting.")
    exit()

# === Load your data ===
df = pd.read_csv(input_filename, sep=";", encoding="utf-8", low_memory=False)

# Ensure the timestamp column is parsed as datetime
df['Timestamp'] = pd.to_datetime(df['Timestamp'])

# === Filter only bio_ecg columns ===
# ecg_cols = [col for col in df.columns if col.lower().startswith("bio_ecg")]
ecg_cols = []  # Initialize an empty list to store ECG column names
for cols in df.columns:
    print(cols)  # Debugging: print all column names
    for col in cols.split(";"):
        if col.lower().startswith("bio_ecg"):
            ecg_cols.append(col)
df_ecg = df[ecg_cols]

# === Remove duplicate rows ===
df_ecg = df_ecg.drop_duplicates()

# === Drop rows where all ECG values are empty ===
df_ecg = df_ecg.dropna(how='all')

# === Prepare output storage ===
all_rows = []

# === Process each row individually ===
SAMPLING_RATE = 130  # Hz
SAMPLE_PERIOD = 1 / SAMPLING_RATE  # seconds per sample

for index, row in df_ecg.iterrows():
    values = row.dropna().values  # drop any NaNs if partial rows
    num_samples = len(values)

    if num_samples == 0:
        continue  # skip empty rows

    # Use the timestamp value from the row as the starting point
    start_time = df.loc[index, 'Timestamp']

    # Generate timestamps starting from the row's timestamp
    timestamps = [start_time + timedelta(seconds=i * SAMPLE_PERIOD) for i in range(num_samples)]

    # Create temporary DataFrame
    temp_df = pd.DataFrame({
        "timestamp": timestamps,
        "value": values
    })

    all_rows.append(temp_df)

# === Concatenate all pieces together ===
result = pd.concat(all_rows, ignore_index=True)

# === Save to new CSV ===
output_filename = input_filename.replace(".csv", "_ecg.csv")
result.to_csv(output_filename, index=False)

print(f"Saved processed ECG data to {output_filename}")
