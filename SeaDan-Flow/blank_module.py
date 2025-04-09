import numpy as np
import math
from tqdm import tqdm
from scipy.spatial import cKDTree
import laspy
import open3d as o3d
from tkinter import filedialog

def calculate_grid_median_with_kdtree(points, x_min, y_min, col_width, row_width, n_rows, n_cols):
    # Create a KD-tree for fast querying (only using x, y coordinates)
    kdtree = cKDTree(points[:, :2])  # Only use x, y for the KD-tree
    
    avg_alt_mat = np.full((n_rows, n_cols), np.nan, dtype=np.float32)
    point_counts = np.zeros((n_rows, n_cols), dtype=int)
    
    for row in tqdm(range(n_rows)):
        for col in range(n_cols):
            # Define cell boundaries
            x0 = x_min + col * col_width
            x1 = x0 + col_width
            y0 = y_min + row * row_width
            y1 = y0 + row_width
            
            # Query points within the cell bounds, only if the region is non-empty
            cell_center = [(x0 + x1) / 2, (y0 + y1) / 2]
            max_dist = math.sqrt((col_width / 2) ** 2 + (row_width / 2) ** 2)
            cell_indices = kdtree.query_ball_point(cell_center, max_dist)
            
            if len(cell_indices) == 0:  # Skip if there are no points in the vicinity
                continue
            
            # Filter points that actually lie within the cell bounds
            cell_points = points[cell_indices]
            cell_points = cell_points[
                (cell_points[:, 0] >= x0) & (cell_points[:, 0] < x1) &
                (cell_points[:, 1] >= y0) & (cell_points[:, 1] < y1)
            ]
            
            # If there are points in the cell, calculate the median altitude
            if cell_points.size > 0:
                avg_alt_mat[row, col] = np.median(cell_points[:, 2])
                point_counts[row, col] = cell_points.shape[0]

    return avg_alt_mat, point_counts

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
        
def rotate_cloud(vis, pcd, axis="x"):
    if axis == "x":
        axis_values = (np.pi / 24, 0, 0)
    elif axis == "y":
        axis_values = (0, np.pi / 24, 0)
    elif axis == "z":
        axis_values = (0, 0, np.pi / 24)

    rotation = pcd.get_rotation_matrix_from_xyz(axis_values)
    pcd.rotate(rotation)
    vis.update_geometry(pcd)

def move_cloud(vis, pcd, direction, matrix, step):
    translation = np.eye(4)
    
    if direction == "left":
        matrix[0, 3] -= step
        translation[0, 3] -= step
    elif direction == "right":
        matrix[0, 3] += step
        translation[0, 3] += step
    elif direction == "up":
        matrix[1, 3] += step
        translation[1, 3] += step
    elif direction == "down":
        matrix[1, 3] -= step
        translation[1, 3] -= step
    elif direction == "forward":
        matrix[2, 3] += step
        translation[2, 3] += step
    elif direction == "backward":
        matrix[2, 3] -= step
        translation[2, 3] -= step

    pcd.transform(translation)
    vis.update_geometry(pcd)

def key_callback_1(vis, pcd2, matrix2, step):
    vis.register_key_callback(65, lambda vis: move_cloud(vis, pcd2, "left", matrix2, step))     #A
    vis.register_key_callback(68, lambda vis: move_cloud(vis, pcd2, "right", matrix2, step))    #D
    vis.register_key_callback(87, lambda vis: move_cloud(vis, pcd2, "up", matrix2, step))       #W
    vis.register_key_callback(83, lambda vis: move_cloud(vis, pcd2, "down", matrix2, step))     #S
    vis.register_key_callback(88, lambda vis: rotate_cloud(vis, pcd2, "x"))                     #X
    vis.register_key_callback(89, lambda vis: rotate_cloud(vis, pcd2, "y"))                     #Y
    vis.register_key_callback(90, lambda vis: rotate_cloud(vis, pcd2, "z"))                     #Z
    vis.register_key_callback(81, lambda vis: move_cloud(vis, pcd2, "forward", matrix2, step))  #Q
    vis.register_key_callback(69, lambda vis: move_cloud(vis, pcd2, "backward", matrix2, step)) #E