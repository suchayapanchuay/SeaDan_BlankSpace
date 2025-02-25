import open3d as o3d
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from scipy.spatial import cKDTree

def visualize_volume(pcd1_path, pcd2_path, threshold_min, threshold_max):
    print(f"Loading {pcd1_path} and {pcd2_path}...")

    pcd1 = o3d.io.read_point_cloud(pcd1_path)
    pcd2 = o3d.io.read_point_cloud(pcd2_path)

    if len(pcd1.points) == 0 or len(pcd2.points) == 0:
        print("[Error] One or both point clouds are empty.")
        sys.exit(1)

    pcd2_copy = pcd2

    points1 = np.asarray(pcd1.points)
    points2 = np.asarray(pcd2.points)

    # ใช้ KD-Tree เพื่อจับคู่จุดที่ใกล้ที่สุด
    tree = cKDTree(points1[:, :2])  
    distances, indices = tree.query(points2[:, :2])  

    valid_mask = distances < 1.0  

    matched_points1 = points1[indices[valid_mask]]  
    matched_points2 = points2[valid_mask]  

    delta_alt = matched_points2[:, 2] - matched_points1[:, 2]

    norm1 = Normalize(vmin=float(threshold_min), vmax=float(threshold_max))
    colormap = plt.get_cmap('bwr')  
    colors = colormap(norm1(delta_alt))[:, :3]  

    new_colors = np.zeros_like(points2)  
    new_colors[valid_mask] = colors  

    pcd2_copy.colors = o3d.utility.Vector3dVector(new_colors)  

    print("Opening Volume Change Visualization...")
    o3d.visualization.draw_geometries([pcd2_copy])

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python visualize_volume.py <pcd1_file> <pcd2_file> <threshold_min> <threshold_max>")
        sys.exit(1)
    
    pcd1_file = sys.argv[1]
    pcd2_file = sys.argv[2]
    threshold_min = sys.argv[3]
    threshold_max = sys.argv[4]

    visualize_volume(pcd1_file, pcd2_file, threshold_min, threshold_max)
