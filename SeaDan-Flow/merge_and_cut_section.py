import laspy
import numpy as np
from blank_module import convert_o3d_pcd2las
import open3d as o3d
import os

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

time_series1 = {}
time_series2 = {}
output_dir = ""

def process_las_region(time_series1, time_series2, region_min, region_max, batch_size=500_000):
    x_min, y_min = region_min
    x_max, y_max = region_max

    part_points, part_colors = [], []
    block_points, block_colors = [], []

    for name, file_path in time_series1.items():
        with laspy.open(file_path) as las_file:
            for las_chunk in las_file.chunk_iterator(batch_size):
                mask = (
                    (las_chunk.x >= x_min) & (las_chunk.x <= x_max) &
                    (las_chunk.y >= y_min) & (las_chunk.y <= y_max)
                )
                if np.any(mask):
                    points = np.vstack((las_chunk.x[mask], las_chunk.y[mask], las_chunk.z[mask])).T
                    colors = np.vstack((las_chunk.red[mask], las_chunk.green[mask], las_chunk.blue[mask])).T / 65536
                    part_points.append(points)
                    part_colors.append(colors)

    for name, file_path in time_series2.items():
        with laspy.open(file_path) as las_file:
            for las_chunk in las_file.chunk_iterator(batch_size):
                mask = (
                    (las_chunk.x >= x_min) & (las_chunk.x <= x_max) &
                    (las_chunk.y >= y_min) & (las_chunk.y <= y_max)
                )
                if np.any(mask):
                    points = np.vstack((las_chunk.x[mask], las_chunk.y[mask], las_chunk.z[mask])).T
                    colors = np.vstack((las_chunk.red[mask], las_chunk.green[mask], las_chunk.blue[mask])).T / 65536
                    block_points.append(points)
                    block_colors.append(colors)

    if part_points and block_points:
        part_points = np.vstack(part_points)
        part_colors = np.vstack(part_colors)
        block_points = np.vstack(block_points)
        block_colors = np.vstack(block_colors)

        pcd_part = o3d.geometry.PointCloud()
        pcd_part.points = o3d.utility.Vector3dVector(part_points)
        pcd_part.colors = o3d.utility.Vector3dVector(part_colors)
        convert_o3d_pcd2las(pcd_part, os.path.join(output_dir, "Time_Series1_SelectedRegion.las"))

        pcd_block = o3d.geometry.PointCloud()
        pcd_block.points = o3d.utility.Vector3dVector(block_points)
        pcd_block.colors = o3d.utility.Vector3dVector(block_colors)
        convert_o3d_pcd2las(pcd_block, os.path.join(output_dir, "Time_Series2_SelectedRegion.las"))

        print("✅ Finished extracting the selected region.")
        messagebox.showinfo("Success", "Done")
    else:
        print(f"No data in range")

# ---------------- GUI ------------------

def select_time_series1():
    global time_series1
    paths = filedialog.askopenfilenames(title="Select Time Series 1 files", filetypes=[("LAS files", "*.las")])
    time_series1 = {f"Part{i}": path for i, path in enumerate(paths)}
    ts1_label.config(text=f"Selected {len(paths)} Time Series 1 files")

def select_time_series2():
    global time_series2
    paths = filedialog.askopenfilenames(title="Select Time Series 2 files", filetypes=[("LAS files", "*.las")])
    time_series2 = {f"Block_{i}": path for i, path in enumerate(paths)}
    ts2_label.config(text=f"Selected {len(paths)} Time Series 2 files")

def select_output_folder():
    global output_dir
    output_dir = filedialog.askdirectory(title="Select Output Folder")
    output_label.config(text=f"Output Folder: {output_dir}")

def run_processing():
    if not time_series1 or not time_series2 or not output_dir:
        messagebox.showerror("Error", "กรุณาเลือกไฟล์และโฟลเดอร์ให้ครบ")
        return

    try:
        x1 = float(x1_var.get())
        y1 = float(y1_var.get())
        x2 = float(x2_var.get())
        y2 = float(y2_var.get())
    except ValueError:
        messagebox.showerror("Error", "กรุณาใส่พิกัดให้ถูกต้อง (ตัวเลขเท่านั้น)")
        return

    x_min, x_max = min(x1, x2), max(x1, x2)
    y_min, y_max = min(y1, y2), max(y1, y2)

    process_las_region(time_series1, time_series2, region_min=(x_min, y_min), region_max=(x_max, y_max))

# ---------------- Create GUI ------------------

root = tk.Tk()
root.title("Cut Selected Region from LAS")
root.geometry("600x350")

ts_frame = tk.LabelFrame(root, text="Time Series Files")
ts_frame.pack(fill="x", padx=10, pady=5)

ts1_label = tk.Label(ts_frame, text="ยังไม่ได้เลือก Time Series 1")
ts1_label.grid(row=0, column=0, sticky='w', padx=5)
ttk.Button(ts_frame, text="เลือก Time Series 1", command=select_time_series1).grid(row=0, column=1, padx=5)

ts2_label = tk.Label(ts_frame, text="ยังไม่ได้เลือก Time Series 2")
ts2_label.grid(row=1, column=0, sticky='w', padx=5)
ttk.Button(ts_frame, text="เลือก Time Series 2", command=select_time_series2).grid(row=1, column=1, padx=5)

output_frame = tk.LabelFrame(root, text="Output")
output_frame.pack(fill="x", padx=10, pady=5)

output_label = tk.Label(output_frame, text="ยังไม่ได้เลือก Output Folder")
output_label.grid(row=0, column=0, sticky='w', padx=5)
ttk.Button(output_frame, text="เลือกโฟลเดอร์ Output", command=select_output_folder).grid(row=0, column=1, padx=5)

coord_frame = tk.LabelFrame(root, text="ระบุพิกัดที่ต้องการตัด (x1, y1) → (x2, y2)")
coord_frame.pack(fill="x", padx=10, pady=5)

x1_var = tk.StringVar(); y1_var = tk.StringVar()
x2_var = tk.StringVar(); y2_var = tk.StringVar()

tk.Label(coord_frame, text="x1:").grid(row=0, column=0, padx=5, pady=2.5)
tk.Entry(coord_frame, textvariable=x1_var).grid(row=0, column=1, padx=5)
tk.Label(coord_frame, text="y1:").grid(row=0, column=2, padx=5)
tk.Entry(coord_frame, textvariable=y1_var).grid(row=0, column=3, padx=5)

tk.Label(coord_frame, text="x2:").grid(row=1, column=0, padx=5)
tk.Entry(coord_frame, textvariable=x2_var).grid(row=1, column=1, padx=5)
tk.Label(coord_frame, text="y2:").grid(row=1, column=2, padx=5)
tk.Entry(coord_frame, textvariable=y2_var).grid(row=1, column=3, padx=5)

ttk.Button(root, text="✅ merge & cut", command=run_processing).pack(pady=10)

root.mainloop()