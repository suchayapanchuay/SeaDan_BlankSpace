import laspy
import numpy as np
from blank_module import convert_o3d_pcd2las
import open3d as o3d
import os

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

chunk_size_var = None  # Global สำหรับเก็บค่าจาก input box
time_series1 = {}
time_series2 = {}
output_dir = ""

def process_las_chunked(time_series1, time_series2, min_Part, max_Part, min_Block, max_Block, glb_min, glb_max, chunk_size, batch_size, axis="X"):

    step = (glb_max - glb_min) / chunk_size

    for i in range(chunk_size):
        start = glb_min + (i * step)
        end = start + step

        part_points, part_colors = [], []
        block_points, block_colors = [], []

        # อ่านไฟล์ Part ทีละ Batch
        for j, (part_name, file_path) in enumerate(time_series1.items()):
            part_min, part_max = min_Part[j], max_Part[j]

            if part_min < end and part_max >= start:
                with laspy.open(file_path) as las_file:
                    for las_chunk in las_file.chunk_iterator(batch_size):
                        coords = {"X": las_chunk.x, "Y": las_chunk.y, "Z": las_chunk.z}
                        mask = (coords[axis] >= start) & (coords[axis] < end)
                        
                        if np.any(mask):  # ถ้ามีจุดในช่วงนี้
                            points = np.vstack((las_chunk.x[mask], las_chunk.y[mask], las_chunk.z[mask])).T
                            colors = np.vstack((las_chunk.red[mask], las_chunk.green[mask], las_chunk.blue[mask])).T / 65536
                            part_points.append(points)
                            part_colors.append(colors)

        # อ่านไฟล์ Block ทีละ Batch
        for k, (block_name, block_file_path) in enumerate(time_series2.items()):
            block_min, block_max = min_Block[k], max_Block[k]

            if block_min < end and block_max > start:
                with laspy.open(block_file_path) as las_file:
                    for las_chunk in las_file.chunk_iterator(batch_size):
                        coords = {"X": las_chunk.x, "Y": las_chunk.y, "Z": las_chunk.z}
                        mask = (coords[axis] >= start) & (coords[axis] < end)
                        
                        if np.any(mask):
                            points = np.vstack((las_chunk.x[mask], las_chunk.y[mask], las_chunk.z[mask])).T
                            colors = np.vstack((las_chunk.red[mask], las_chunk.green[mask], las_chunk.blue[mask])).T / 65536

                            block_points.append(points)
                            block_colors.append(colors)

        if part_points and block_points:
            print(f"Processing chunk {i}: X = {start} - {end}")

            part_points = np.vstack(part_points)
            part_colors = np.vstack(part_colors)
            block_points = np.vstack(block_points)
            block_colors = np.vstack(block_colors)

            # Convert Part to Open3D
            pcd_part = o3d.geometry.PointCloud()
            pcd_part.points = o3d.utility.Vector3dVector(part_points)
            pcd_part.colors = o3d.utility.Vector3dVector(part_colors)
            part_output_path = os.path.join(output_dir, f"Time_Series1_{i}_Merged.las")
            # part_output_path = os.path.join(output_dir, f"Time_Series1_{i+1}_Merged.las")
            convert_o3d_pcd2las(pcd_part, part_output_path)

            # Convert Block to Open3D
            pcd_block = o3d.geometry.PointCloud()
            pcd_block.points = o3d.utility.Vector3dVector(block_points)
            pcd_block.colors = o3d.utility.Vector3dVector(block_colors)
            block_output_path = os.path.join(output_dir, f"Time_Series2_{i}_Merged.las")
            # block_output_path = os.path.join(output_dir, f"Time_Series2_{i+1}_Merged.las")
            convert_o3d_pcd2las(pcd_block, block_output_path)

        else:
            print(f"Skipping chunk {i} (No data in this range)")

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
    try:
        chunk_size = int(chunk_size_var.get())
    except ValueError:
        messagebox.showerror("Error", "Chunk size ต้องเป็นเลขจำนวนเต็ม")
        return

    if not time_series1 or not time_series2 or not output_dir:
        messagebox.showerror("Error", "กรุณาเลือกไฟล์และโฟลเดอร์ให้ครบ")
        return

    # อ่านค่าขอบเขต
    x_min_Part, x_max_Part, y_min_Part, y_max_Part = [], [], [], []
    x_min_Block, x_max_Block, y_min_Block, y_max_Block = [], [], [], []

    for part_name, file_path in time_series1.items():
        las = laspy.read(file_path)
        min_x, min_y, _ = las.header.min
        max_x, max_y, _ = las.header.max
        x_min_Part.append(min_x)
        x_max_Part.append(max_x)
        y_min_Part.append(min_y)
        y_max_Part.append(max_y)

    for block_name, block_file_path in time_series2.items():
        las = laspy.read(block_file_path)
        min_x, min_y, _ = las.header.min
        max_x, max_y, _ = las.header.max
        x_min_Block.append(min_x)
        x_max_Block.append(max_x)
        y_min_Block.append(min_y)
        y_max_Block.append(max_y)

    if axis_var.get() == "X":
        glb_min = min(min(x_min_Part), min(x_min_Block))
        glb_max = max(max(x_max_Part), max(x_max_Block))
        min_Part = x_min_Part
        max_Part = x_max_Part
        min_Block = x_min_Block
        max_Block = x_max_Block
    elif axis_var.get() == "Y":
        glb_min = min(min(y_min_Part), min(y_min_Block))
        glb_max = max(max(y_max_Part), max(y_max_Block))
        min_Part = y_min_Part
        max_Part = y_max_Part
        min_Block = y_min_Block
        max_Block = y_max_Block

    # เรียก function ที่มีอยู่แล้ว
    process_las_chunked(
        time_series1, time_series2,
        min_Part, max_Part,
        min_Block, max_Block,
        glb_min, glb_max,
        chunk_size=chunk_size, batch_size=500_000,
        axis=axis_var.get()
    )

    messagebox.showinfo("Success", "การประมวลผลเสร็จสิ้น")

root = tk.Tk()
root.title("LAS Chunking Tool")
root.geometry("500x250")

ts_frame = tk.LabelFrame(root, text="time series1 & time series2")
ts_frame.grid(row=0, column=0, sticky='we', padx=10, pady=5)
ts1_label = tk.Label(ts_frame, text="ยังไม่ได้เลือก Time Series 1")
ts1_label.grid(row=0, column=0, sticky='w', padx=5, pady=2.5)
ts1_btn = ttk.Button(ts_frame, text="เลือก Time Series 1", command=select_time_series1)
ts1_btn.grid(row=0, column=1, sticky="we", padx=5, pady=2.5)

ts2_label = tk.Label(ts_frame, text="ยังไม่ได้เลือก Time Series 2")
ts2_label.grid(row=1, column=0, sticky='w', padx=5, pady=2.5)
ts2_btn = ttk.Button(ts_frame, text="เลือก Time Series 2", command=select_time_series2)
ts2_btn.grid(row=1, column=1, sticky='we', padx=5, pady=2.5)


output_frame = tk.LabelFrame(root, text="output")
output_frame.grid(row=1, column=0, padx=10, pady=5)

output_label = tk.Label(output_frame, text="ยังไม่ได้เลือก Output Folder")
output_label.grid(row=0, column=0, sticky='w', padx=5, pady=2.5)
output_path_btn = ttk.Button(output_frame, text="เลือกโฟลเดอร์ Output", command=select_output_folder)
output_path_btn.grid(row=0, column=1, sticky='we', padx=5, pady=2.5)

chunk_size_label = tk.Label(output_frame, text="Chunk Size (default = 60)").grid(row=1, column=0, sticky='w', padx=5, pady=2.5)
chunk_size_var = tk.StringVar(value="60")
tk.Entry(output_frame, textvariable=chunk_size_var).grid(row=1, column=1, sticky='we', padx=5, pady=2.5)

axis_label = tk.Label(output_frame, text="เลือกแกนในการตัด")
axis_label.grid(row=2, column=0, sticky='w', padx=5, pady=2.5)

axis_var = tk.StringVar(value="X")
axis_options = ttk.Combobox(output_frame, textvariable=axis_var, values=["X", "Y"], state="readonly")
axis_options.grid(row=2, column=1, sticky='we', padx=5, pady=2.5)

merge_n_cut_btn = ttk.Button(output_frame, text="merge & cut", command=run_processing).grid(row=3, column=1, sticky='we', padx=5, pady=2.5)

root.mainloop()