import os
import open3d as o3d
import laspy
import numpy as np
import matplotlib.path as matplotlibpath
import time
import copy

"""
NOTE: To use this script, a segmented and aligned point cloud dataset is required for input.

Use 
- Set target building's LOD2 object name into the 'input_building_list' list. Multiple names can be inserted.
    -- To process all buildings in an area, use 'get_building_list_in_polygon.py' to create a list of building names.
- a footprint polygon table for the same buildings (created by 'create_footprint_polygons.py' and 'neighbor_minding_polygon_expansion.py'),
- a LiDAR dataset in LAS format,
- a bounds file for that same dataset (created by 'create_dataset_bounding_box_list.py')
to separate all data related to the buildings in the dataset, and align the data so that all overlapping scans fit correctly over each other.
Both the aligned and unaligned versions of the building point clouds are outputted.
"""


building_polygons_file    = "S:/OSS/Data/Footprints/test_footprint_2_0m_dilation.txt"
bounds_file               = "S:/OSS/Data/las_bounds.txt"
input_dataset_path        = "S:/OSS/Data/Test_segmented_data/"
aligned_output_path       = "S:/OSS/Data/Aligned_point_clouds/"
unaligned_output_path     = "S:/OSS/Data/Unaligned_point_clouds/"

visualize_alignment_steps = False
radius_normal             = 0.4
matching_resolution       = 0.02
    force_las_output          = True

input_building_list       = ["building_349.obj"] # Insert comma-separated building object files.



def main():
    
    print("\n\nList of buildings to process:")
    print(input_building_list)
    print("\n")
    
    # Go through each building and search the input dataset for points inside their large-dilation footprint polygons
    with open(building_polygons_file, 'r') as polygon_file:
        process_start_time = time.time()
        
        polygon_file_data = polygon_file.readlines()
        total_building_count_in_dataset = len(polygon_file_data)
        processed_buildings = 0
        buildings_to_process = len(input_building_list)

        for data_number in range(0,total_building_count_in_dataset):

            # Check polygon file data against the list of buildings to process
            building_data = polygon_file_data[data_number]
            words = building_data.split()
            lod2_filename = str(words[0])
            if lod2_filename not in input_building_list:
                continue

            # Get output name
            print("Processing LOD2 file '%s' (%d/%d)..." % (lod2_filename, (processed_buildings+1), buildings_to_process) )
            output_point_cloud_filename = str(words[1])
            if force_las_output == True:
                output_point_cloud_filename = output_point_cloud_filename[:-4] + ".las"
                
            # Check if output exists already
            complete_output_filename = os.path.join( aligned_output_path, output_point_cloud_filename )
            if os.path.exists(complete_output_filename) == True:
                print("  output file already exists. Skipping this building...")
                continue

            # Get point clouds from the LiDAR dataset that might contain building data
            building_start_time = time.time()
            nodes = []
            for node_number in range(2, len(words), 2):
                node_position = [ float(words[node_number]), float(words[node_number+1]) ]
                nodes.append(node_position)
            point_cloud_file_list = search_las_dataset(nodes)
            
            # Get all the target building points from the chosen point clouds and process
            if len(point_cloud_file_list) > 0:
                combine_points_in_target_polygon(point_cloud_file_list, nodes, output_point_cloud_filename)
                elapsed_building_time = time.time() - building_start_time
                print("All input data for this building processed. Total elapsed time: {num} seconds".format(num=elapsed_building_time))                
            else:
                print(" No points found for this building...")
                
            processed_buildings += 1
        elapsed_process_time = time.time() - process_start_time
        print("All input data for this building processed. Total elapsed time: {num} seconds".format(num=elapsed_process_time))
    print("Done")
    
    
def search_las_dataset(target_polygon):
    """
    Get a list of las files that contain data in the target polygon coordinates.
    Note: It is possible that the target polygon's points won't be inside the .las file's bounding box, but some of its edges still cross it. Ignoring this case as an outlier for now.
    
    Parameters
    ----------
    target_polygon : List<[Numpy.array]>
        List of 2D points that define a closed polygon in the horizontal plane, enclosing the target building
    
    Returns
    -------
    aligned_lidar_point_clouds : List<Open3D.geometry.PointCloud>
        Building point clouds, aligned against each other
    unaligned_lidar_point_clouds : List<Open3D.geometry.PointCloud>
        Building point clouds, unaligned, as they were scanned.
    """
    start_time = time.time()
    file_list = []
    print( "Searching for candidate point clouds..." )
    with open(bounds_file, 'r') as f:
        data = f.readlines()
        for line in data:
            words = line.split()
            filename = str(words[0])
            min_x = float(words[1])
            min_y = float(words[2])            
            max_x = float(words[4])
            max_y = float(words[5])            
            polygon_point_count = len(target_polygon) # How many coordinate pairs
            for i in range(polygon_point_count):    
                coordinates = target_polygon[i]
                if coordinates[0] > min_x and coordinates[0] < max_x:
                    if coordinates[1] > min_y and coordinates[1] < max_y:
                        print("  Found file: %s" % filename )
                        file_list.append(filename)
                        break
                    
    elapsed_time = time.time() - start_time
    print( "Collected %d files, elapsed time: %f seconds" % (len(file_list), elapsed_time) )
    return file_list


def combine_points_in_target_polygon(file_list, target_polygon, output_name):
    """
    Get the actual points belonging to the building in the input point clouds, and then proceed to align the chosen points against each other.
        
    Parameters
    ----------
    file_list : List<string>
        List of point cloud files whose bounding boxes cross the target building polygon (might or might not contain data on the actual building)
    target_polygon : List<[Numpy.array]>
        List of 2D points that define a closed polygon in the horizontal plane, enclosing the target building
    output_name : string
        Filename to output results into
    """
    
    inside_points_list = []
    print( "Masking points in each candidate file with the target polygon..." )
    for i in range(len(file_list)):
        
        start_time = time.time()
        input_file = os.path.join( input_dataset_path, file_list[i] )
        print( "  point cloud #{num}: {name}...".format(num=i, name=input_file) )
        
        las = laspy.read(input_file)
        xyz = np.vstack([las.x, las.y, las.z]).transpose()
        xy = np.vstack([las.x, las.y]).transpose()
        point_cloud_ids = las.user_data
        point_cloud_ids = np.asarray(point_cloud_ids)
        point_cloud_ids = np.reshape(point_cloud_ids, (-1,1))
        labels = las.classification
        labels = np.asarray(labels)
        labels = np.reshape(labels, (-1, 1))
        
        path = matplotlibpath.Path(target_polygon)
        in_out_points = path.contains_points(xy)
        print("    calculated in/out mask...")
        inside_points = []
        inside_point_cloud_ids = []
        inside_labels = []
        
        inside_points = np.asarray(xyz[in_out_points])
        inside_point_cloud_ids = np.asarray(point_cloud_ids[in_out_points])
        inside_labels = np.asarray(labels[in_out_points])
        
        print( "    found %d points" % len(inside_points) )
        if len(inside_points) > 0:
            inside_points_list.append([inside_points, inside_point_cloud_ids, inside_labels])            
        
        elapsed_time = time.time() - start_time
        print("      elapsed time:", elapsed_time)
        
    if len(inside_points_list) == 0:
        print("  No points found that belong to the target building. Moving on to the next one...")
        return
    
    # Align points
    if len(inside_points_list) > 1:
        print("  Aligning point clouds...")
        aligned_point_clouds, unaligned_point_clouds = align_point_clouds( inside_points_list )
    else:
        print("  A single file contained points belonging to the target building. No alignment necessary.")
        point_cloud_data = inside_points_list[0]
        point_cloud = o3d.geometry.PointCloud()
        point_cloud.points = o3d.utility.Vector3dVector( np.asarray(point_cloud_data[0]) )
        aligned_point_clouds = []
        aligned_point_clouds.append(point_cloud)
        
    # Combine data
    aligned_combined_point_cloud = None
    unaligned_combined_point_cloud = None
    combined_ids = None
    combined_labels = None
    for point_cloud_num in range(len(aligned_point_clouds)):
        aligned_point_cloud = aligned_point_clouds[point_cloud_num]
        unaligned_point_cloud = unaligned_point_clouds[point_cloud_num]
        if aligned_combined_point_cloud == None:
            aligned_combined_point_cloud = aligned_point_cloud
            unaligned_combined_point_cloud = unaligned_point_cloud
            combined_ids = inside_points_list[point_cloud_num][1]
            combined_labels = inside_points_list[point_cloud_num][2]
        else:
            aligned_combined_point_cloud = aligned_combined_point_cloud + aligned_point_cloud
            unaligned_combined_point_cloud = unaligned_combined_point_cloud + unaligned_point_cloud
            combined_ids = np.append(combined_ids, inside_points_list[point_cloud_num][1], axis=0)
            combined_labels = np.append(combined_labels, inside_points_list[point_cloud_num][2], axis=0)

    aligned_points   = np.asarray(aligned_combined_point_cloud.points)
    unaligned_points = np.asarray(unaligned_combined_point_cloud.points)
    ids              = np.asarray(combined_ids)
    labels           = np.asarray(combined_labels)
    
    aligned_points   = aligned_points.reshape((-1, 3))
    unaligned_points = unaligned_points.reshape((-1, 3))
    ids              = ids.reshape((-1))
    labels           = labels.reshape((-1))
    
    # Output data to file
    print( "All point clouds processed, with %d points collected." % len(aligned_points))
    aligned_output_name = "aligned_" + output_name
    full_output_filename = os.path.join( aligned_output_path, aligned_output_name )
    write_point_cloud(full_output_filename, aligned_points, ids, labels)
    unaligned_output_name = "unaligned_" + output_name
    full_output_filename = os.path.join( unaligned_output_path, unaligned_output_name )
    write_point_cloud(full_output_filename, unaligned_points, ids, labels)
    
    
    
def write_point_cloud(output_name, points, ids, labels):
    """
    Parameters
    ----------
    output_name : string
        Name of the output file, including full path.
    points : Numpy.array
        Array of points ([N,3]) to be outputted.
    ids : Numpy.array
        Array of point cloud IDs ([N,1]) same size as the ''points' array. Written into the las file's 'user_data' field to differentiate between originating point clouds.
    labels : Numpy.array
        Array of point labels ([N,1]) same size as the 'points' array. Written into the las file's 'classification' field and contains labels given by segmentation model.
    """
    if output_name.endswith(".ply"):
        print( "Writing data to point cloud: '%s'" % (output_name) )
        point_cloud = o3d.geometry.PointCloud()
        point_cloud.points = o3d.utility.Vector3dVector(points)
        o3d.io.write_point_cloud(output_name, point_cloud, write_ascii=False, compressed=False, print_progress=True)
    elif output_name.endswith(".las"):
        print( "Writing data to point cloud: '%s'" % (output_name) )
        header = laspy.LasHeader(point_format=3, version="1.4")
        header.scale = [0.001, 0.001, 0.001]
        las = laspy.LasData(header)
        all_x = points[:,0]
        all_y = points[:,1]
        all_z = points[:,2]
        las.x = all_x
        las.y = all_y
        las.z = all_z
        las.user_data = ids
        las.classification = labels        
        las.write(output_name)
    else:
        print( "Unsupported output file type! (%s)" % output_name)
        

def align_point_clouds( inside_points_list ):
    """
    Align each point cloud in the input list one at a time against the combination of all the other point clouds.
    The maximum amount a single point cloud can move is several meters, incorrect alignments are controlled by having a strict maximum RMS error requirement.
    
    Parameters
    ----------
    inside_points_list : List<List<numpy.array, numpy.array, numpy.array>>
        List of list of arrays containing data drawn from various LiDAR scans. First element contains the point cloud points, and is the only one relevant to this function.
    
    Returns
    -------
    aligned_lidar_point_clouds : List<Open3D.geometry.PointCloud>
        Building point clouds, aligned against each other
    unaligned_lidar_point_clouds : List<Open3D.geometry.PointCloud>
        Building point clouds, unaligned, as they were scanned.
    """
    
    unaligned_lidar_point_clouds = []
    aligned_lidar_point_clouds = []
    downsampled_lidar_point_clouds = []
    
    for point_cloud_num in range(len(inside_points_list)):
        point_cloud_data = inside_points_list[point_cloud_num]
        points = point_cloud_data[0]
        point_cloud = o3d.geometry.PointCloud()
        point_cloud.points = o3d.utility.Vector3dVector(points)
        downsampled_point_cloud = o3d.geometry.PointCloud.voxel_down_sample(point_cloud, 0.2)
        aligned_lidar_point_clouds.append(point_cloud)
        unaligned_lidar_point_clouds.append( copy.deepcopy(point_cloud) )
        downsampled_lidar_point_clouds.append(downsampled_point_cloud)
        
    lidar_matching_max_distance = 5.0 # Very large matching distance allows for fixing large position errors, pretty safe to use, when combined with low maximum error for accepting the result
    transformation_init_guess = np.identity(4)    

    # Next, combine every point cloud other than one, and adjust that one cloud towards the whole of the rest, if the error of adjusted point cloud is small enough
    print("Seeing if any of the point clouds can or should be adjusted...")
    for moving_num in range(len(downsampled_lidar_point_clouds)):
        downsampled_moving_point_cloud = downsampled_lidar_point_clouds[moving_num]
        static_point_cloud = None
        for static_num in range(len(downsampled_lidar_point_clouds)):
            if static_num == moving_num:
                continue
            if static_point_cloud == None:
                static_point_cloud = downsampled_lidar_point_clouds[static_num]
            else:
                static_point_cloud = static_point_cloud + downsampled_lidar_point_clouds[static_num]
        alignment_result = refine_registration_point_to_point(downsampled_moving_point_cloud, static_point_cloud, transformation_init_guess, lidar_matching_max_distance, 200)
        if alignment_result.inlier_rmse < 0.25:
            #if alignment_result.inlier_rmse < 0.0001:
            print("  Point cloud #{num1}, error={num2}, adjusting pose".format(num1=moving_num, num2=alignment_result.inlier_rmse))
            aligned_lidar_point_clouds[moving_num].transform(alignment_result.transformation)
            downsampled_lidar_point_clouds[moving_num].transform(alignment_result.transformation)
        else:
            print("  Point cloud #{num1}, error={num2}, skipping.".format(num1=moving_num, num2=alignment_result.inlier_rmse))
      
    print("Matching process completed.")
    return aligned_lidar_point_clouds, unaligned_lidar_point_clouds



def refine_registration_point_to_point(moving, reference, initial_transformation, distance_threshold=1.0, max_iteration=100):
    result = o3d.pipelines.registration.registration_icp( moving, reference, distance_threshold, initial_transformation, 
                                                          o3d.pipelines.registration.TransformationEstimationPointToPoint(), 
                                                          o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=max_iteration))
    return result



if __name__ == '__main__':
    main()
