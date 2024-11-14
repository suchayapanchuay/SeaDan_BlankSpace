import multiprocessing
import numpy as np
import open3d as o3d
import matplotlib.pyplot as plt
import laspy
import math
import time
from tqdm import tqdm
from scipy.spatial import cKDTree

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


if __name__ == "__main__":
    # Load source point cloud
    source_path = r".\\Dataset\\Beach_1\\source-beach-1-cut.las"
    with laspy.open(source_path) as fh:
        print('Points from Header:', fh.header.point_count)
        source = fh.read()
        print('Points from data:', len(source.points))

    scaling_fac = 1
    source_coords = np.vstack((source.x * scaling_fac, source.y * scaling_fac, source.z * scaling_fac)).T
    source_pcd = o3d.geometry.PointCloud()
    source_pcd.points = o3d.utility.Vector3dVector(source_coords)

    # Load target point cloud
    target_path = r".\\Dataset\\Beach_1\\target-beach-1-cut.las"
    with laspy.open(target_path) as fh :
        print('Points from Header:', fh.header.point_count)
        target = fh.read()
        print('Points from data:', len(target.points))

    target_coords = np.vstack((target.x * scaling_fac, target.y * scaling_fac, target.z * scaling_fac)).T
    target_pcd = o3d.geometry.PointCloud()
    target_pcd.points = o3d.utility.Vector3dVector(target_coords)

    # Extract point coordinates
    src_points = np.asarray(source_pcd.points)
    tgt_points = np.asarray(target_pcd.points)

    # Bounding box and grid setup
    src_x_min, src_x_max = min(src_points[:, 0]), max(src_points[:, 0])
    src_y_min, src_y_max = min(src_points[:, 1]), max(src_points[:, 1])
    tgt_x_min, tgt_x_max = min(tgt_points[:, 0]), max(tgt_points[:, 0])
    tgt_y_min, tgt_y_max = min(tgt_points[:, 1]), max(tgt_points[:, 1])

    gbl_x_min, gbl_x_max = min(src_x_min, tgt_x_min), max(src_x_max, tgt_x_max)
    gbl_y_min, gbl_y_max = min(src_y_min, tgt_y_min), max(src_y_max, tgt_y_max)

    col_width = 1
    row_width = 1

    n_cols = math.ceil((gbl_x_max - gbl_x_min) / col_width)
    n_rows = math.ceil((gbl_y_max - gbl_y_min) / row_width)

    start_time = time.perf_counter()

    # Prepare argument tuples for multiprocessing
    src_args = (src_points, gbl_x_min, gbl_y_min, col_width, row_width, n_rows, n_cols)
    tgt_args = (tgt_points, gbl_x_min, gbl_y_min, col_width, row_width, n_rows, n_cols)

    if n_cols*n_rows < 1 :
        # Use multiprocessing to calculate median altitudes for both source and target
        with multiprocessing.Pool(processes = 4) as pool:
            # starmap will unpack each tuple argument list correctly
            results = pool.starmap(calculate_grid_median_with_kdtree, [src_args, tgt_args])
        
        # Unpack results
        src_avg_alt_mat, count_point_src = results[0]
        tgt_avg_alt_mat, count_point_tgt = results[1]
        
    else :

        src_avg_alt_mat, count_point_src = calculate_grid_median_with_kdtree(src_points, gbl_x_min, gbl_y_min, col_width, row_width, n_rows, n_cols)
        tgt_avg_alt_mat, count_point_tgt = calculate_grid_median_with_kdtree(tgt_points, gbl_x_min, gbl_y_min, col_width, row_width, n_rows, n_cols)

    print(count_point_src)
    print(count_point_tgt)
    # Delta altitude matrix and volume change calculation
    delta_alt_mat = tgt_avg_alt_mat - src_avg_alt_mat

    cell_area = col_width * row_width
    volume_change = (np.array(tgt_avg_alt_mat) - np.array(src_avg_alt_mat)) * cell_area

    volume_change = np.nan_to_num(volume_change)
    total_volume_change = np.sum(volume_change)
    
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time

    # Plotting results
    #fig = plt.figure()
    fig, ax = plt.subplots()
    im = ax.imshow(src_avg_alt_mat)
    ax.set_title('Average Altitude (Source)')
    ax.set_xlabel(f'{n_cols} columns')
    ax.set_ylabel(f'{n_rows} rows')
    plt.show()
    
    fig, ax = plt.subplots()
    im = ax.imshow(tgt_avg_alt_mat)
    ax.set_title('Average Altitude (Target)')
    ax.set_xlabel(f'{n_cols} columns')
    ax.set_ylabel(f'{n_rows} rows')
    plt.show()

    fig, ax = plt.subplots()
    im = ax.imshow(delta_alt_mat)
    ax.set_title('Delta Altitude (Target - Source)')
    ax.set_xlabel(f'{n_cols} columns')
    ax.set_ylabel(f'{n_rows} rows')
    plt.show()
    
    print(f'Total volume change: {total_volume_change:.10f} cubic units')
    print(f"Elapsed time with KD-tree optimization: {elapsed_time:.4f} seconds")