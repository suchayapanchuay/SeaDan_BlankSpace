import open3d as o3d
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

def apply_colormap(pcd, colormap_name='viridis_r'):
    points = np.asarray(pcd.points)
    
    if len(points) == 0:
        print("[Error] No points found in the point cloud.")
        return
    
    z_values = points[:, 2]  
    colormap = plt.get_cmap(colormap_name)
    normalized_z = (z_values - np.min(z_values)) / (np.max(z_values) - np.min(z_values))
    colors = colormap(normalized_z)[:, :3] 
    pcd.colors = o3d.utility.Vector3dVector(colors)

def visualize_pcd(file_path, title, apply_cmap):
    print(f"Loading {file_path} for {title}")
    pcd = o3d.io.read_point_cloud(file_path)

    if len(pcd.points) == 0:
        print(f"[Error] No points in {file_path}")
        sys.exit(1)

    if apply_cmap.lower() == "true":
        print("Applying colormap...")
        apply_colormap(pcd)  

    o3d.visualization.draw_geometries([pcd], window_name=title)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python visualize_color.py <point_cloud_file> <title> <apply_cmap>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    title = sys.argv[2]
    apply_cmap = sys.argv[3]  # รับค่าเป็น string ("true"/"false")
    
    visualize_pcd(file_path, title, apply_cmap)
