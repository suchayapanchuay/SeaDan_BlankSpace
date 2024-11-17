import numpy as np
import math
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