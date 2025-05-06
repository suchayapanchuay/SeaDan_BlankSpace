import numpy as np
import laspy
import open3d as o3d 
# open3d รองรับแค่ Python 3.7 - 3.11 (ณ ตอนนี้)
import os
from blank_module import convert_o3d_pcd2las
import tkinter as tk
from tkinter import filedialog

def process_las_chunked(time_series1, time_series2, x_min_Part, x_max_Part, x_min_Block, x_max_Block, glb_x_min, glb_x_max, chunk_size, batch_size):
    step_x = (glb_x_max - glb_x_min) / chunk_size  

    for i in range(chunk_size):
        start_x = glb_x_min + (i * step_x)
        end_x = start_x + step_x

        part_points, part_colors = [], []
        block_points, block_colors = [], []

        # อ่านไฟล์ Part ทีละ Batch
        for j, (part_name, file_path) in enumerate(time_series1.items()):
            min_x, max_x = x_min_Part[j], x_max_Part[j]

            if min_x < end_x and max_x >= start_x:
                with laspy.open(file_path) as las_file:
                    for las_chunk in las_file.chunk_iterator(batch_size):
                        mask = (las_chunk.x >= start_x) & (las_chunk.x < end_x)
                        
                        if np.any(mask):  # ถ้ามีจุดในช่วงนี้
                            points = np.vstack((las_chunk.x[mask], las_chunk.y[mask], las_chunk.z[mask])).T
                            colors = np.vstack((las_chunk.red[mask], las_chunk.green[mask], las_chunk.blue[mask])).T / 65536

                            part_points.append(points)
                            part_colors.append(colors)

        # อ่านไฟล์ Block ทีละ Batch
        for k, (block_name, block_file_path) in enumerate(time_series2.items()):
            min_x, max_x = x_min_Block[k], x_max_Block[k]

            if min_x < end_x and max_x > start_x:
                with laspy.open(block_file_path) as las_file:
                    for las_chunk in las_file.chunk_iterator(batch_size):
                        mask = (las_chunk.x >= start_x) & (las_chunk.x < end_x)
                        
                        if np.any(mask):
                            points = np.vstack((las_chunk.x[mask], las_chunk.y[mask], las_chunk.z[mask])).T
                            colors = np.vstack((las_chunk.red[mask], las_chunk.green[mask], las_chunk.blue[mask])).T / 65536

                            block_points.append(points)
                            block_colors.append(colors)

        if part_points and block_points:
            print(f"Processing chunk {i}: X = {start_x} - {end_x}")

            part_points = np.vstack(part_points)
            part_colors = np.vstack(part_colors)
            block_points = np.vstack(block_points)
            block_colors = np.vstack(block_colors)

            # Convert Part to Open3D
            pcd_part = o3d.geometry.PointCloud()
            pcd_part.points = o3d.utility.Vector3dVector(part_points)
            pcd_part.colors = o3d.utility.Vector3dVector(part_colors)
            part_output_path = os.path.join(output_dir, f"Time_Series1_{i}_Merged.las")
            convert_o3d_pcd2las(pcd_part, part_output_path)

            # Convert Block to Open3D
            pcd_block = o3d.geometry.PointCloud()
            pcd_block.points = o3d.utility.Vector3dVector(block_points)
            pcd_block.colors = o3d.utility.Vector3dVector(block_colors)
            block_output_path = os.path.join(output_dir, f"Time_Series2_{i}_Merged.las")
            convert_o3d_pcd2las(pcd_block, block_output_path)

        else:
            print(f"Skipping chunk {i} (No data in this range)")

root = tk.Tk()
root.withdraw()

part_file_paths = filedialog.askopenfilenames(title="Select all Time_series 1 files (*.las)", filetypes=[("LAS files", "*.las")])
time_series1 = {f"Part{i}": path for i, path in enumerate(part_file_paths)}

block_file_paths = filedialog.askopenfilenames(title="Select all Time_series 2 files(*.las)", filetypes=[("LAS files", "*.las")])
time_series2 = {f"Block_{i}": path for i, path in enumerate(block_file_paths)}

# เลือก Output Directory
output_dir = filedialog.askdirectory(title="Select Output Folder")
if not output_dir:
    raise Exception("ไม่ได้เลือกโฟลเดอร์ปลายทาง")

os.makedirs(output_dir, exist_ok=True)

x_min_Part = []
x_max_Part = []
y_min_Part = []
y_max_Part = []
x_min_Block = []
x_max_Block = []
y_min_Block = []
y_max_Block = []

for part_name, file_path in time_series1.items():
        las = laspy.read(file_path)
        min_x, min_y, min_z = las.header.min
        max_x, max_y, max_z = las.header.max

        x_min_Part.append(min_x)
        x_max_Part.append(max_x)
        y_min_Part.append(min_y)
        y_max_Part.append(max_y)

        print(f"{part_name} Min (X, Y, Z): ({min_x}, {min_y}, {min_z})")
        print(f"{part_name} Max (X, Y, Z): ({max_x}, {max_y}, {max_z})")
        print("-" * 70)

for block_name, block_file_path in time_series2.items():
        las = laspy.read(block_file_path)
        min_x, min_y, min_z = las.header.min
        max_x, max_y, max_z = las.header.max

        x_min_Block.append(min_x)
        x_max_Block.append(max_x)
        y_min_Block.append(min_y)
        y_max_Block.append(max_y)
        print(f"{block_name} Min (X, Y, Z): ({min_x}, {min_y}, {min_z})")
        print(f"{block_name} Max (X, Y, Z): ({max_x}, {max_y}, {max_z})")
        print("-" * 70)
    
global_x_min_Part = min(x_min_Part)
global_x_max_Part = max(x_max_Part)
global_y_min_Part = min(y_min_Part)
global_y_max_Part = max(y_max_Part)

global_x_min_Block = min(x_min_Block)
global_x_max_Block = max(x_max_Block)
global_y_min_Block = min(y_min_Block)
global_y_max_Block = max(y_max_Block)

glb_x_min = min(global_x_min_Part,global_x_min_Block)
glb_x_max = max(global_x_max_Part,global_x_max_Block)
glb_y_min = min(global_y_min_Part,global_y_min_Block)
glb_y_max = max(global_y_max_Part,global_y_max_Block)

print(f"Global Min Part (X, Y): ({global_x_min_Part}, {global_y_min_Part})")
print(f"Global Max Part (X, Y): ({global_x_max_Part}, {global_y_max_Part})")
print(f"Global Min Block (X, Y): ({global_x_min_Block}, {global_y_min_Block})")
print(f"Global Max Block (X, Y): ({global_x_max_Block}, {global_y_max_Block})")
print("-" * 70)
print(f"Overall Global Min (X, Y): ({glb_x_min}, {glb_y_min})")
print(f"Overall Global Max (X, Y): ({glb_x_max}, {glb_y_max})")

    
# output_dir = "E:\\beach\\Merged_file"
# os.makedirs(output_dir, exist_ok=True)


process_las_chunked(time_series1, time_series2, x_min_Part, x_max_Part, x_min_Block, x_max_Block, glb_x_min, glb_x_max, chunk_size=60, batch_size=500_000)