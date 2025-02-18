import laspy
import open3d as o3d
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import math
from calculate_volume import calculate_grid_median_with_kdtree
import multiprocessing 
import time
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from PIL import Image, ImageTk, ImageSequence
import threading
import queue
from matplotlib import cm
from scipy.spatial import cKDTree
import copy

class O3DVisualizer:
    def __init__(self):
        self.windows = {}
        self.threads = {}
        
    def create_window(self, pcd, title, width=1024, height=768):
        vis = o3d.visualization.Visualizer()
        vis.create_window(window_name=title, width=width, height=height)
        vis.add_geometry(pcd)
        
        # Set default view
        ctr = vis.get_view_control()
        ctr.set_zoom(0.8)
        ctr.set_front([0, 0, -1])
        ctr.set_lookat([0, 0, 0])
        ctr.set_up([0, 1, 0])
        
        return vis
        
    def run_visualization(self, vis, window_id):
        try:
            vis.run()
        finally:
            vis.destroy_window()
            if window_id in self.windows:
                del self.windows[window_id]
            if window_id in self.threads:
                del self.threads[window_id]
    
    def show_pointcloud(self, pcd, title, apply_cmap=False, colormap_name='viridis_r'):
        try:
            # Save original colors
            original_colors = np.asarray(pcd.colors).copy() if pcd.colors else None
            
            # Apply colormap if requested
            if apply_cmap:
                points = np.asarray(pcd.points)
                z_values = points[:, 2]
                colormap = plt.get_cmap(colormap_name)
                normalized_z = (z_values - np.min(z_values)) / (np.max(z_values) - np.min(z_values))
                colors = colormap(normalized_z)[:, :3]
                pcd.colors = o3d.utility.Vector3dVector(colors)
            
            # Create unique window ID
            window_id = f"{title}_{len(self.windows)}"
            
            # Create and store visualizer
            vis = self.create_window(pcd, title)
            self.windows[window_id] = vis
            
            # Create and start visualization thread
            thread = threading.Thread(target=self.run_visualization, args=(vis, window_id))
            self.threads[window_id] = thread
            thread.start()
            
            # Restore original colors if needed
            if original_colors is not None:
                pcd.colors = o3d.utility.Vector3dVector(original_colors)
            
            return window_id
            
        except Exception as e:
            messagebox.showwarning("Error", f"Visualization error: {str(e)}")
            return None
            
    def show_volume_change(self, pcd1, pcd2, threshold_min=-0.1, threshold_max=0.1):
        try:
            pcd2_copy = copy.deepcopy(pcd2)
            points1 = np.asarray(pcd1.points)
            points2 = np.asarray(pcd2.points)
            
            # Create KD-tree for point matching
            tree = cKDTree(points1[:, :2])
            distances, indices = tree.query(points2[:, :2])
            
            # Filter good matches
            valid_mask = distances < 1.0
            matched_points1 = points1[indices[valid_mask]]
            matched_points2 = points2[valid_mask]
            
            # Calculate height differences
            delta_alt = matched_points2[:, 2] - matched_points1[:, 2]
            
            # Create colormap
            norm = Normalize(vmin=threshold_min, vmax=threshold_max)
            colormap = cm.get_cmap('bwr')
            colors = colormap(norm(delta_alt))[:, :3]
            
            # Apply colors to point cloud
            new_colors = np.zeros_like(points2)
            new_colors[valid_mask] = colors
            pcd2_copy.colors = o3d.utility.Vector3dVector(new_colors)
            
            # Show in new window
            return self.show_pointcloud(pcd2_copy, "Volume Change")
            
        except Exception as e:
            messagebox.showwarning("Error", f"Volume change visualization error: {str(e)}")
            return None
    
    def close_window(self, window_id):
        if window_id in self.windows:
            self.windows[window_id].destroy_window()
            del self.windows[window_id]
            if window_id in self.threads:
                self.threads[window_id].join()
                del self.threads[window_id]
    
    def close_all_windows(self):
        for window_id in list(self.windows.keys()):
            self.close_window(window_id)

def read_las_file(file_path):
    las = laspy.read(file_path)
    points = np.vstack((las.x, las.y, las.z)).transpose()
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    return las, pcd

def las2Array(lasdata):
    points = np.vstack((lasdata.x, lasdata.y, lasdata.z)).transpose()
    
    if hasattr(lasdata, 'red') and hasattr(lasdata, 'green') and hasattr(lasdata, 'blue'):
        colors = np.vstack((lasdata.red, lasdata.green, lasdata.blue)).transpose()
        colors = colors / 65535.0 
    else:
        colors = np.ones((len(points), 3))
    
    return points, colors

def pickfile(sot):
    file_path = filedialog.askopenfilename(title=f"Select a {sot} file", filetypes=[("Las file", "*.las")])
    if file_path:
        print(f"Selected file: {file_path}")
        return file_path
    else:
        print("No file selected")
        return None

def create_gui():
    root = tk.Tk()
    root.title("SeaDan")
    root.geometry("1000x1000")
    
    bg_image = Image.open('/Users/suchayapanchuay/Documents/Project/blankspace/image/Background.jpg')
    bg_image = bg_image.resize((1000, 1000))
    bg_photo = ImageTk.PhotoImage(bg_image)
    
    bg_label = tk.Label(root, image=bg_photo)
    bg_label.place(relwidth=1, relheight=1)
 
    image = Image.open('/Users/suchayapanchuay/Documents/Project/blankspace/image/Main_Logo.png')
    image = image.resize((100, 100))
    photo = ImageTk.PhotoImage(image)
    
    header_frame = tk.Frame(root, bg="#FFF9F0")
    header_frame.place(relx=0.5, rely=0.07, anchor="center", width=1000, height=185) 
    
    image_label = tk.Label(root, image=photo,bg='#FFF9F0')
    image_label.image = photo
    image_label.grid(row=0, column=0,columnspan=2, pady=(7, 0), padx=20, sticky="n")
      
    header_label = tk.Label(root, text="Welcome to SeaDan", font=("Helvetica", 21, 'bold'),bg='#FFF9F0',fg="#0F2573") 
    header_label.grid(row=1, column=0, columnspan=2, pady=5, padx=20, sticky="n")
    
    pcd1 = None
    pcd2 = None
    step_value = tk.DoubleVar(value=0.05)
    last_loaded_file1 = None  
    last_loaded_file2 = None
    visualizer = O3DVisualizer()
    
    def load_file1():
        nonlocal pcd1,last_loaded_file1
        file_path = pickfile("source")
        if file_path:
            if file_path == last_loaded_file1:  
                messagebox.showinfo("Info", "File 1 is already loaded.")
                return

            try:
                las_data, pcd = read_las_file(file_path)
                points, colors = las2Array(las_data)
                pcd.points = o3d.utility.Vector3dVector(points)
                pcd.colors = o3d.utility.Vector3dVector(colors)
                pcd1 = pcd
                last_loaded_file1 = file_path  
                load_btn1.config(fg="green")  
                messagebox.showinfo("Success", "File 1 loaded successfully!")
            except Exception as e:
                load_btn1.config(fg="red")  
                messagebox.showerror("Error", f"Failed to load file: {e}")

    def load_file2():
        nonlocal pcd2,last_loaded_file2
        file_path = pickfile("target")
        if file_path:
            if file_path == last_loaded_file2:  
                messagebox.showinfo("Info", "File 2 is already loaded.")
                return

            try:
                las_data, pcd = read_las_file(file_path)
                points, colors = las2Array(las_data)
                pcd.points = o3d.utility.Vector3dVector(points)
                pcd.colors = o3d.utility.Vector3dVector(colors)
                pcd2 = pcd
                last_loaded_file2 = file_path  
                load_btn2.config(fg="green")  
                messagebox.showinfo("Success", "File 2 loaded successfully!")
            except Exception as e:
                load_btn2.config(fg="red")  
                messagebox.showerror("Error", f"Failed to load file: {e}")

    def visualize_a_point_cloud(pcd, title, apply_cmap=False):
        if pcd is not None:
            return visualizer.show_pointcloud(pcd, title, apply_cmap)
        else:
            messagebox.showwarning("Error", "Please load a LAS file first")
            return None

    def view_all(pcd1, pcd2):
        if pcd1 is not None and pcd2 is not None:
            return visualizer.show_volume_change(pcd1, pcd2)
        else:
            messagebox.showwarning("Error", "Please load both LAS files first")
            return None

    load_btn1 = tk.Button(root, text="Load Time Series1", command=load_file1, width=20, height=2)
    load_btn1.grid(row=2, column=0, pady=10, padx=10)

    load_btn2 = tk.Button(root, text="Load Time Series2", command=load_file2, width=20, height=2)
    load_btn2.grid(row=2, column=0, columnspan=2, pady=10)
    
    step_label = tk.Label(root, text="Step value", font=("Helvetica", 14,"bold"), bg="#F0C38E", fg="#0F2573")
    step_label.grid(row=3,column=0, columnspan=2, pady=10)

    step_entry = tk.Entry(root, textvariable=step_value)
    step_entry.grid(row=4,column=0, columnspan=2, pady=10)

    start_vis_source = tk.Button(root, text="Start Visualization Time Series1", 
                                command=lambda: visualize_a_point_cloud(pcd1, "Time Series1"),
                                width=22, height=2)
    start_vis_target = tk.Button(root, text="Start Visualization Time Series2", 
                                command=lambda: visualize_a_point_cloud(pcd2, "Time Series2"),
                                width=22, height=2)
    
    start_vis_source.grid(row=6,pady=10, padx=5)
    start_vis_target.grid(row=6,column=0, columnspan=2, pady=10)

    def on_closing():
        visualizer.close_all_windows()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Start the main Tkinter event loop
    root.mainloop()

if __name__ == "__main__":
    create_gui()
