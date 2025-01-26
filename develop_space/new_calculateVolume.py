import numpy as np
import open3d as o3d
import matplotlib.pyplot as plt
import laspy
import copy
import json
import math
import time

o3d.utility.set_verbosity_level(o3d.utility.VerbosityLevel.Debug)

def draw_registration_result(source, target, transformation):
    source_temp = copy.deepcopy(source)
    target_temp = copy.deepcopy(target)
    source_temp.paint_uniform_color([1, 0.706, 0])
    target_temp.paint_uniform_color([0, 0.651, 0.929])
    source_temp.transform(transformation)

    o3d.visualization.draw_geometries([source_temp, target_temp])
def ICP_registration(source_pcd, target_pcd):
    trans_init = np.asarray([[1, 0, 0, -0.08],
                             [0, 1, 0, -0.02],
                             [0, 0, 1, -0.02], 
                             [0, 0, 0, 1]])
    
    draw_registration_result(source_pcd, target_pcd, trans_init)

    # Apply point-to-point ICP
    threshold = 0.05  # Set the distance threshold for ICP
    reg_p2p = o3d.pipelines.registration.registration_icp(
        source_pcd, target_pcd, threshold, trans_init,
        o3d.pipelines.registration.TransformationEstimationPointToPoint(),
        o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=20))

    print("Transformation matrix from ICP:")
    print(reg_p2p.transformation)

    # Visualize the result after ICP
    draw_registration_result(source_pcd, target_pcd, reg_p2p.transformation)
    return reg_p2p
def pick_points(pcd):
    print("")
    print("1) Please pick at least three correspondences using [shift + left click]")
    print("   Press [shift + right click] to undo point picking")
    print("2) After picking points, press 'Q' to close the window")
    vis = o3d.visualization.VisualizerWithEditing()
    vis.create_window()
    vis.add_geometry(pcd)
    vis.run()  # user picks points
    vis.destroy_window()
    print("")
    return vis.get_picked_points()

def register_via_correspondences(source, target, source_points, target_points):
    corr = np.zeros((len(source_points), 2))
    corr[:, 0] = source_points
    corr[:, 1] = target_points

    # Estimate rough transformation using correspondences
    print("Compute a rough transform using the correspondences given by user")
    p2p = o3d.pipelines.registration.TransformationEstimationPointToPoint(50)
    trans_init = p2p.compute_transformation(source, target, o3d.utility.Vector2iVector(corr))

    # Point-to-point ICP for refinement
    print("Perform point-to-point ICP refinement")
    threshold = 0.4  #3cm distance threshold
    reg_p2p = o3d.pipelines.registration.registration_icp(source, target, threshold, trans_init,o3d.pipelines.registration.TransformationEstimationPointToPoint())
    return reg_p2p

def create_bounding_box(center, width, height, depth):
    # Adjust box creation to ensure correct representation
    box = o3d.geometry.TriangleMesh.create_box(width, height, depth)
    box.translate(center - np.array([width / 2, height / 2, depth / 2]))
    return box.get_oriented_bounding_box()

def visualize_grid_with_bounding_boxes(n_rows, n_cols, gbl_x_min, gbl_x_max, gbl_y_min, gbl_y_max, 
                                       src_avg_alt_mat, tgt_avg_alt_mat):
    col_width = (gbl_x_max - gbl_x_min) / n_cols
    row_width = (gbl_y_max - gbl_y_min) / n_rows

    geometries = []

    for row in range(n_rows):
        for col in range(n_cols):
            avg_alt_src = src_avg_alt_mat[row, col]
            avg_alt_tgt = tgt_avg_alt_mat[row, col]

            if np.isnan(avg_alt_src) or np.isnan(avg_alt_tgt):
                continue

            delta_alt = avg_alt_tgt - avg_alt_src
            box_depth = delta_alt if delta_alt > 0 else -delta_alt
            center_z = min(avg_alt_src, avg_alt_tgt) + box_depth / 2

            center_x = gbl_x_min + col * col_width + col_width / 2
            center_y = gbl_y_min + row * row_width + row_width / 2

            bounding_box = create_bounding_box(center=np.array([center_x, center_y, center_z]), 
                                               width=col_width, height=row_width, depth=box_depth)
            bounding_box.color = [1, 0, 0] if delta_alt > 0 else [0, 0, 1]
            geometries.append(bounding_box)

    o3d.visualization.draw_geometries(geometries)

if __name__ == "__main__":
    start = time.time()
    # Load source point cloud
    source_path = r'./Dataset/sand.las'
    with laspy.open(source_path) as fh:
        print('Points from Header:', fh.header.point_count)
        source = fh.read()
        print('Points from data:', len(source.points))

    scaling_fac = 1
    source_coords = np.vstack((source.x*scaling_fac, source.z*scaling_fac, source.y*scaling_fac))
    source_colors = np.vstack((source.red, source.green, source.blue))
    source_pcd = o3d.geometry.PointCloud()
    source_pcd.points = o3d.utility.Vector3dVector(source_coords.transpose())
    source_pcd.colors = o3d.utility.Vector3dVector(source_colors.transpose()/65536)

    # Load target point cloud
    target_path = r"./Dataset/sand.las"
    with laspy.open(target_path) as fh:
        print('Points from Header:', fh.header.point_count)
        target = fh.read()
        print('Points from data:', len(target.points))

    target_coords = np.vstack((target.x*scaling_fac, target.z*scaling_fac, target.y*scaling_fac))
    target_colors = np.vstack((target.red, target.green, target.blue))
    target_pcd = o3d.geometry.PointCloud()
    target_pcd.points = o3d.utility.Vector3dVector(target_coords.transpose())
    target_pcd.colors = o3d.utility.Vector3dVector(target_colors.transpose()/65536)

    # registration ource and target
    # source_points = pick_points(source_pcd)
    # target_points = pick_points(target_pcd)

    # assert (len(source_points) >= 3 and len(target_points) >= 3)
    # assert (len(source_points) == len(target_points))
    # reg_p2p = register_via_correspondences(source_pcd, target_pcd, source_points, target_points)
    # print("best tranformation : ",reg_p2p.transformation)
    # trans_registration = reg_p2p.transformation

    #regitration ICP
    # ICP = ICP_registration(source_pcd, target_pcd)
    # trans_registration = ICP.transformation

    #All grid = 50 , 50 (50,100,150)

    trans_regstration_sand = np.array([[ 0.97918502, -0.20274252,  0.00960066, -0.30185095],
     [ 0.20281223, 0.97919306, -0.00693921,  0.27977106],
     [-0.00799402, 0.0087419,   0.99992983, -0.03252387],
     [ 0.,          0.,          0.,          1.        ]])
    
    trans_registration = trans_regstration_sand

    ## volume 500  = 0.0009396756
    # trans_regstration_500 = np.array([[ 0.99953977, -0.02912603, -0.00848035, -0.05608813],
    #                                   [ 0.0290906,   0.99956766, -0.00427065, -0.0340945 ],
    #                                   [ 0.00860107,  0.00402199,  0.99995492,  0.04429181],
    #                                   [ 0.,          0.,          0.,          1.,        ]])
    
    # trans_registration = trans_regstration_500

    #volume 1000  =
    # trans_regstration_1000 = np.array([[ 0.99952279, -0.02610147, -0.01651972, -0.11588954],
    #                                   [ 0.02602306,  0.99964912, -0.0049437,   0.02576701],
    #                                   [ 0.01664296,  0.00451145,  0.99985132,  0.04641928],
    #                                   [ 0.,          0.,          0.,          1.        ]])
    
    # trans_registration = trans_regstration_1000

    #volume 1500 = 
    # trans_registration_1500 = np.array([[ 0.97462249, -0.02808296, -0.01302552, -0.15376139],
    #                                    [ 0.02801394,  0.97469697, -0.005325,   -0.05620635],
    #                                    [ 0.01317331,  0.00494811,  0.97501246,  0.04069209],
    #                                    [ 0.,          0.,          0.,         1.        ]])
    
    # trans_registration = trans_registration_1500

    #volume 2000 = 0.0013342820
    # trans_registration_2000 = np.array([[ 0.99986951, -0.0062386,  -0.01490137, -0.07952318],
    #                                     [ 0.00607626,  0.99992197, -0.01091492, -0.0199495 ],
    #                                     [ 0.0149683,   0.01082296,  0.99982939,  0.03641272],
    #                                     [ 0.,          0.,          0.,          1.        ]])
    
    # trans_registration = trans_registration_2000

    #volume 2500
    # trans_registration_2500 = np.array([[ 0.99990506, -0.00236401, -0.01357517, -0.07726428],
    #                                     [ 0.00222993,  0.99994867, -0.0098837,  -0.13971217],
    #                                     [ 0.01359784,  0.00985249,  0.999859 ,   0.03637949],
    #                                     [ 0.,         0.,          0.,          1.        ]])
    
    # trans_registration = trans_registration_2500
    
    #volume 3000
    # trans_registration_3000 = np.array([[ 0.99974266,-0.01522442, -0.01681768, -0.08377408],
    #                                     [ 0.01512831,  0.99986858, -0.00582754, -0.10072416],
    #                                     [ 0.01690419,  0.00557162,  0.99984159,  0.03288217],
    #                                     [ 0.,          0.,          0.,          1.        ]])

    # trans_registration = trans_registration_3000

    #volume 3500
    # trans_registration_3500 = np.array([[ 0.99853616, -0.00160803, -0.05406432, -0.13051229],
    #                                     [ 0.00221839,  0.99993447,  0.01123128, -0.07907413],
    #                                     [ 0.05404272, -0.01133477,  0.99847429,  0.04680669],
    #                                     [ 0.,          0.,          0.,          1.        ]])

    # trans_registration = trans_registration_3500

    #volume 4000
    # trans_registration_4000 = np.array([[ 0.99813861,  0.02978051, -0.05322071, -0.12142175],
    #                                     [-0.02935881,  0.99953118,  0.00868817, -0.06112408],
    #                                     [ 0.0534545,  -0.0071095,   0.99854498,  0.02904755],
    #                                     [ 0.,          0.,          0.,          1.        ]])

    # trans_registration = trans_registration_4000


    #volume 4500
    # trans_registration_4500 = np.array([[ 9.97975834e-01, -2.40379488e-03, -6.35488529e-02, -1.11105181e-01],
    #                                     [ 2.44795032e-03,  9.99996813e-01,  6.16974793e-04, -6.87769495e-02],
    #                                     [ 6.35471673e-02, -7.71290368e-04,  9.97978538e-01,  2.84434206e-02],
    #                                     [ 0.00000000e+00,  0.00000000e+00,  0.00000000e+00,  1.00000000e+00]])

    # trans_registration = trans_registration_4500

    #volume 5000
    # trans_registration_5000 = np.array([[ 0.9986187,  -0.00909988, -0.05174831, -0.11932266],
    #                                     [ 0.00977298, 0.99987071,  0.01276911,  0.00146753],
    #                                     [ 0.05162542, -0.01325721,  0.99857852,  0.02988235],
    #                                     [ 0.,          0.,          0.,          1.        ]])

    # trans_registration = trans_registration_5000

    # match lang:
    # case "JavaScript":
    #     print("You can become a web developer.")

    # case "Python":
    #     print("You can become a Data Scientist")

    # case "PHP":
    #     print("You can become a backend developer")

    # case "Solidity":
    #     print("You can become a Blockchain developer")

    # case "Java":
    #     print("You can become a mobile app developer")
    # case _:
    #     print("The language doesn't matter, what matters is solving problems.")

    source_temp = copy.deepcopy(source_pcd)
    target_temp = copy.deepcopy(target_pcd)
    source_temp.transform(trans_registration)
    #target_temp.transform(trans_regstration)

    o3d.visualization.draw_geometries([source_temp, target_temp])

    # Extract point coordinates
    src_points = np.asarray(source_temp.points)
    tgt_points = np.asarray(target_temp.points)

    # Bounding box and grid setup
    src_x_min, src_x_max = min(src_points[:, 0]), max(src_points[:, 0])
    src_y_min, src_y_max = min(src_points[:, 1]), max(src_points[:, 1])
    src_z_min, src_z_max = min(src_points[:, 2]), max(src_points[:, 2])

    tgt_x_min, tgt_x_max = min(tgt_points[:, 0]), max(tgt_points[:, 0])
    tgt_y_min, tgt_y_max = min(tgt_points[:, 1]), max(tgt_points[:, 1])
    tgt_z_min, tgt_z_max = min(tgt_points[:, 2]), max(tgt_points[:, 2])

    gbl_x_min, gbl_x_max = min(src_x_min, tgt_x_min), max(src_x_max, tgt_x_max)
    gbl_y_min, gbl_y_max = min(src_y_min, tgt_y_min), max(src_y_max, tgt_y_max)
    gbl_z_min, gbl_z_max = min(src_z_min, tgt_z_min), max(src_z_max, tgt_z_max)

    print(f'        source      target   :   global ')
    print(f'MinX {src_x_min} {tgt_x_min} : {gbl_x_min}')
    print(f'MaxX {src_x_max} {tgt_x_max} : {gbl_x_max}')
    print(f'MinY {src_y_min} {tgt_y_min} : {gbl_y_min}')
    print(f'MaxY {src_y_max} {tgt_y_max} : {gbl_y_max}')
    print(f'MinZ {src_z_min} {tgt_z_min} : {gbl_z_min}')
    print(f'MaxZ {src_z_max} {tgt_z_max} : {gbl_z_max}')

    # Grid dimensions
    n_cols, n_rows = 50,50
    print([gbl_x_min, gbl_y_min, gbl_z_min])
    print([gbl_x_max, gbl_y_max, gbl_z_max])
    print([gbl_x_max-gbl_x_min, gbl_y_max-gbl_y_min, gbl_z_max-gbl_z_min])
    col_width = (gbl_x_max - gbl_x_min) / n_cols
    row_width = (gbl_y_max - gbl_y_min) / n_rows
    print("col width: ", col_width, " , row width: ", row_width)

    # Visualization of source and target point clouds in 3D
    subsample = 10
    src_x = src_points[::subsample, 0]
    src_y = src_points[::subsample, 1]
    src_z = src_points[::subsample, 2]
    src_colors = source_pcd.colors[::subsample]

    fig = plt.figure(figsize=(10, 10))
    ax3D = fig.add_subplot(111, projection='3d')
    ax3D.scatter(src_x, src_y, src_z, s=1, c=src_colors, marker='.')
    ax3D.view_init(elev= 90, azim= -90, roll= 0)
    ax3D.set_xlim(gbl_x_min, gbl_x_max)
    ax3D.set_ylim(gbl_y_min, gbl_y_max)
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('3D projection of source point cloud')
    plt.grid(True)
    plt.show()

    fig = plt.figure(figsize=(10, 10))
    ax3D = fig.add_subplot(111, projection='3d')
    ax3D.scatter(tgt_points[::subsample, 0], tgt_points[::subsample, 1], tgt_points[::subsample, 2], s=1, c=np.asarray(target_pcd.colors)[::subsample], marker='.')
    ax3D.view_init(elev=90, azim=-90, roll=0)
    ax3D.set_xlim(gbl_x_min, gbl_x_max)
    ax3D.set_ylim(gbl_y_min, gbl_y_max)
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('3D projection of target point cloud')
    plt.grid(True)
    plt.show()

    # Grid-based point counting and altitude calculation for source
    src_list_2D = [[[] for _ in range(n_rows)] for _ in range(n_cols)]
    for i, pt in enumerate(source_temp.points):
        #print("print int :",(pt[0] - gbl_x_min) // col_width)
        #print("print int2 :",(pt[1] - gbl_y_min) // row_width)

        col_idx = math.ceil((pt[0] - gbl_x_min) // col_width)
        row_idx = math.ceil((pt[1] - gbl_y_min) // row_width)
        if 0 <= col_idx < n_cols and 0 <= row_idx < n_rows:
            src_list_2D[row_idx][col_idx].append(i)

    src_count_mat = np.array([[len(src_list_2D[j][k]) for k in range(n_cols)] for j in range(n_rows)])

    fig, ax = plt.subplots()
    im = ax.imshow(src_count_mat)
    ax.set_title('No. points in a cell (Source)')
    ax.set_xlabel(f'{n_cols} columns')
    ax.set_ylabel(f'{n_rows} rows')
    plt.show()

    src_avg_alt_mat = np.full((n_rows, n_cols), np.nan)
    for row in range(n_rows):
        for col in range(n_cols):
            idxs = src_list_2D[row][col]
            if len(idxs) > 0:
                 src_avg_alt_mat[row, col] = np.mean(np.asarray(source_temp.points)[idxs, 2])

    fig, ax = plt.subplots()
    im = ax.imshow(src_avg_alt_mat)
    ax.set_title('Average Altitude (Source)')
    ax.set_xlabel(f'{n_cols} columns')
    ax.set_ylabel(f'{n_rows} rows')
    plt.show()

    # Grid-based point counting and altitude calculation for target
    tgt_list_2D = [[[] for _ in range(n_rows)] for _ in range(n_cols)]
    for i, pt in enumerate(target_temp.points):
        col_idx = math.ceil((pt[0] - gbl_x_min) // col_width)
        row_idx = math.ceil((pt[1] - gbl_y_min) // row_width)
        if 0 <= col_idx < n_cols and 0 <= row_idx < n_rows:
            tgt_list_2D[row_idx][col_idx].append(i)

    tgt_count_mat = np.array([[len(tgt_list_2D[j][k]) for k in range(n_cols)] for j in range(n_rows)])

    fig, ax = plt.subplots()
    im = ax.imshow(tgt_count_mat)
    ax.set_title('No. points in a cell (Target)')
    ax.set_xlabel(f'{n_cols} columns')
    ax.set_ylabel(f'{n_rows} rows')
    plt.show()

    tgt_avg_alt_mat = np.full((n_rows, n_cols), np.nan)
    for row in range(n_rows):
        for col in range(n_cols):
            idxs = tgt_list_2D[row][col]
            if len(idxs) > 0:
                 tgt_avg_alt_mat[row, col] = np.mean(np.asarray(target_temp.points)[idxs, 2])

    fig, ax = plt.subplots()
    im = ax.imshow(tgt_avg_alt_mat)
    ax.set_title('Average Altitude (Target)')
    ax.set_xlabel(f'{n_cols} columns')
    ax.set_ylabel(f'{n_rows} rows')
    plt.show()

    src_avg_alt_mat_list = src_avg_alt_mat.tolist()    
    with open('src_avg_alt_mat_list.json', 'w') as json_file:
      json.dump(src_avg_alt_mat_list , json_file)

    tgt_avg_alt_mat_list = tgt_avg_alt_mat.tolist()    
    with open('tgt_avg_alt_mat_list.json', 'w') as json_file:
      json.dump(tgt_avg_alt_mat_list, json_file)

    # Visualize the grid with bounding boxes in 3D
    #visualize_grid_with_bounding_boxes(n_rows, n_cols, gbl_x_min, gbl_x_max, gbl_y_min, gbl_y_max, src_avg_alt_mat, tgt_avg_alt_mat)
    
    # def fill_nan_with_neighbors(matrix):
    #     nan_positions = np.isnan(matrix)
    #     while np.any(nan_positions):   #fix boundary
    #         new_matrix = matrix.copy()
    #         for row in range(matrix.shape[0]):
    #             for col in range(matrix.shape[1]):
    #                 if np.isnan(matrix[row, col]):
    #                     # Collect neighboring values
    #                     neighbors = []
    #                     for i in range(max(0, row - 1), min(row + 2, matrix.shape[0])):
    #                         for j in range(max(0, col - 1), min(col + 2, matrix.shape[1])):
    #                             if not np.isnan(matrix[i, j]):
    #                                 neighbors.append(matrix[i, j])
    #                     # Replace NaN with the average of valid neighbors
    #                     if neighbors:
    #                         new_matrix[row, col] = np.mean(neighbors)
    #         matrix = new_matrix
    #         nan_positions = np.isnan(matrix)
    #     return matrix
    
    def fill_nan_with_neighbors(matrix):
        nan_positions = np.isnan(matrix)
        
        while np.any(nan_positions):
            new_matrix = matrix.copy()
            for row in range(matrix.shape[0]):
                for col in range(matrix.shape[1]):
                    if np.isnan(matrix[row, col]):
                        # up, down, left, right, and diagonally
                        neighbors = []
                        for i in range(max(0, row - 1), min(row + 2, matrix.shape[0])):
                            for j in range(max(0, col - 1), min(col + 2, matrix.shape[1])):
                                if not (i == row and j == col):  
                                    if not np.isnan(matrix[i, j]):  
                                        neighbors.append(matrix[i, j])
                        
                        # Replace NaN with the average of valid neighbors
                        if neighbors:
                            new_matrix[row, col] = np.mean(neighbors)
            
            matrix = new_matrix
            nan_positions = np.isnan(matrix)
        
        return matrix

    # Fill NaN values in the average altitude matrices
    src_avg_alt_mat_filled = fill_nan_with_neighbors(src_avg_alt_mat)
    tgt_avg_alt_mat_filled = fill_nan_with_neighbors(tgt_avg_alt_mat)
    
    delta_alt_mat1 = tgt_avg_alt_mat_filled - src_avg_alt_mat_filled
    delta_alt_mat = tgt_avg_alt_mat - src_avg_alt_mat

    fig, ax = plt.subplots()
    im = ax.imshow(tgt_avg_alt_mat_filled)
    ax.set_title('Filled Delta Altitude Target')
    ax.set_xlabel(f'{n_cols} columns')
    ax.set_ylabel(f'{n_rows} rows')
    plt.show()

    fig, ax = plt.subplots()
    im = ax.imshow(src_avg_alt_mat_filled)
    ax.set_title('Filled Delta Altitude Source)')
    ax.set_xlabel(f'{n_cols} columns')
    ax.set_ylabel(f'{n_rows} rows')
    plt.show()



    tgt_avg_alt_mat = tgt_avg_alt_mat_filled
    src_avg_alt_mat = src_avg_alt_mat_filled 




    # Change in altitude calculation
    
    print(delta_alt_mat)
    volume_change_list = delta_alt_mat.tolist()    
    with open('delta_alt_mat.json', 'w') as json_file:
       json.dump(volume_change_list, json_file)

    fig, ax = plt.subplots()
    im = ax.imshow(delta_alt_mat)
    ax.set_title('Delta Altitude (Target - Source)')
    ax.set_xlabel(f'{n_cols} columns')
    ax.set_ylabel(f'{n_rows} rows')
    plt.show()

    fig, ax = plt.subplots()
    im = ax.imshow(delta_alt_mat1)
    ax.set_title('Delta Altitude (Target - Source)')
    ax.set_xlabel(f'{n_cols} columns')
    ax.set_ylabel(f'{n_rows} rows')
    plt.show()

    #################  calculate 1  ############

    # #Calculate the area of each cell
    # cell_area = col_width * row_width

    # #Calculate volume change for each cell
    # volume_change = np.nan_to_num((delta_alt_mat)*cell_area)

    # total_volume_change = np.sum(volume_change)
    # print(f'Total volume change: {total_volume_change :.10f}')

    # volume_change_list = total_volume_change.tolist()    
    # with open('volume_change.json', 'w') as json_file:
    #    json.dump(volume_change_list, json_file)
  
    ################# calculate 2 ############

    cell_area = col_width* row_width 
    print("Area : ",cell_area)

    # Calculate volume change for each cell (Width, length, height)
    volume_change = (tgt_avg_alt_mat - src_avg_alt_mat) * cell_area
    print("volume_change :",volume_change.shape)

    # Print valid volume change for debugging
    valid_volume_change = np.nan_to_num(volume_change) #np.abs(volume_change)
    print("valid_volume_change :",valid_volume_change.shape)
    print(valid_volume_change)
    volume_change_list = volume_change.tolist()    
    with open('volume_change.json', 'w') as json_file:
      json.dump(volume_change_list, json_file)
    
    total_volume_change = np.sum(valid_volume_change)
    print("total_volume_change :",volume_change.shape)
    print(f"time : {time.time() - start:.5f} sec.")
    print(f'Total volume change: {total_volume_change :.10f} cubic units')
    