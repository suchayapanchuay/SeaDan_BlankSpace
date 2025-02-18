import open3d as o3d
import sys

def visualize_pcd(file_path, title):
    pcd = o3d.io.read_point_cloud(file_path)
    o3d.visualization.draw_geometries([pcd], window_name=title)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python visualize.py <point_cloud_file> <title>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    title = sys.argv[2]
    
    visualize_pcd(file_path, title)
