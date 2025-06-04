import laspy
import open3d as o3d
import numpy as np
import tkinter as tk
from tkinter import filedialog

def load_las_as_o3d(path):
    las = laspy.read(path)
    xyz = np.vstack((las.x, las.y, las.z)).T
    colors = np.vstack((las.red, las.green, las.blue)).T / 65535.0

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(xyz)
    pcd.colors = o3d.utility.Vector3dVector(colors)
    return pcd

def crop_with_box(pcd):
    print("👉 วาดกรอบเลือกจุด (Crop Box) แล้วกด 'C' เพื่อยืนยัน หรือ 'F' เพื่อปิด")
    o3d.visualization.draw_geometries_with_editing([pcd], window_name="เลือกกรอบแล้วกด C")

    print("🧠 ตอนนี้ Open3D ไม่ได้คืนค่ากล่องที่คุณ crop มาให้โดยตรง")
    print("➡️ ดังนั้นเราจะใช้เครื่องมือที่แม่นกว่าด้านล่างแทน")

def crop_with_gui_box(pcd):
    vis = o3d.visualization.VisualizerWithEditing()
    vis.create_window(window_name="Crop Box: วาดกรอบ แล้วกด 'C'")
    vis.add_geometry(pcd)
    vis.run()
    vis.destroy_window()

    picked = vis.get_picked_points()
    points = np.asarray(pcd.points)[picked]

    if len(points) < 2:
        print("⚠️ ต้องเลือกอย่างน้อย 2 จุดเพื่อสร้างกรอบ")
        return

    x_vals = points[:, 0]
    y_vals = points[:, 1]

    x_min, x_max = float(x_vals.min()), float(x_vals.max())
    y_min, y_max = float(y_vals.min()), float(y_vals.max())

    print("\n🎯 พิกัดกรอบที่คุณเลือก:")
    print(f"x1 = {x_min:.6f}")
    print(f"x2 = {x_max:.6f}")
    print(f"y1 = {y_min:.6f}")
    print(f"y2 = {y_max:.6f}")

    return (x_min, y_min), (x_max, y_max)

def main():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title="เลือกไฟล์ LAS", filetypes=[("LAS files", "*.las")])
    if not file_path:
        print("❌ ไม่ได้เลือกไฟล์")
        return

    print(f"📂 Loading: {file_path}")
    pcd = load_las_as_o3d(file_path)
    crop_with_gui_box(pcd)

if __name__ == "__main__":
    main()
