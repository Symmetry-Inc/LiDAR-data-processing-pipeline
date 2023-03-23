import os
import numpy as np
import open3d as o3d
import laspy
import subprocess

"""
Run the iterative Poisson Surface Reconstruction algorithm.
If the input data is far away from the origin, the rounding errors will cause the resulting mesh to be horribly misformed, and so, the point cloud needs to be centered first, and then moved back to its original position, once process finishes.
"""

process_entire_folder = False
building_number       = 349 # If 'process_entire_folder' is set to False, this will define the target building

input_path            = "S:/OSS/Data/Combined_point_clouds/"
output_path           = "S:/OSS/Data/Meshes/"

# Process single file
input_filename        = "combined_building_" + str(building_number) + "_points.las"
output_filename       = "iPSR_mesh_" + str(building_number) + ".ply"


def main():
    
    print("\n\n")
    
    if process_entire_folder == True:
        for root, dirs, files in os.walk( input_path ):
            for filename in files:
                if filename.endswith(".las"):
                    print("Processing point cloud:", filename)
                    
                    # Check for existing files
                    output_name = "mesh_" + filename[17:-10] + ".ply"
                    output_file = os.path.join( output_path, output_name )
                    if os.path.exists(output_file) == True:
                        print("  output file already exist. Skipping building...")
                        continue
                    
                    # Read data
                    input_file = os.path.join( input_path, filename )
                    las = laspy.read(input_file)
                    xyz = np.vstack([las.x, las.y, las.z]).transpose()
                    point_cloud = o3d.geometry.PointCloud()
                    point_cloud.points = o3d.utility.Vector3dVector(xyz)
                    
                    # Center data
                    center = point_cloud.get_center()
                    print("  offset:", center)
                    point_cloud.translate(-center)
                    o3d.io.write_point_cloud("tmp_ipsr_input.ply", point_cloud, write_ascii=False, compressed=False, print_progress=True)
                        
                    # Run iPSR algorithm
                    print("Launching iPSR algorithm in a separate process...")
                    process = subprocess.run(["ipsr.exe", "--in", "tmp_ipsr_input.ply", "--out", "tmp_ipsr_output.ply", "--depth", "8", "--iters", "25", "--pointWeight", "6", "--neighbors", "16"])
                    print("running...")
                    print("Process returned:", process.returncode)
                    
                    # Read the output, and move it back to the original position, then save
                    print("Preparing the output...")    
                    mesh = o3d.io.read_triangle_mesh("tmp_ipsr_output.ply")
                    mesh.translate(center)
                    o3d.io.write_triangle_mesh(output_file, mesh)
                    
                    # Delete the temporary files
                    print("Cleaning up...")
                    os.remove("tmp_ipsr_input.ply")
                    os.remove("tmp_ipsr_output.ply")
    else:
        # Load the input point cloud, center it, and save to a temporary file
        print("Processing point cloud:", input_filename)
        print("Loading the input point cloud and centering it...")
        input_file = os.path.join( input_path, input_filename )
        if input_file.endswith(".ply"):
            point_cloud = o3d.io.read_point_cloud(input_file)
        elif input_file.endswith(".las"):
            las = laspy.read(input_file)
            xyz = np.vstack([las.x, las.y, las.z]).transpose()
            point_cloud = o3d.geometry.PointCloud()
            point_cloud.points = o3d.utility.Vector3dVector(xyz)
        center = point_cloud.get_center()
        print("  offset:", center)
        point_cloud.translate(-center)
        o3d.io.write_point_cloud("tmp_ipsr_input.ply", point_cloud, write_ascii=False, compressed=False, print_progress=True)
            
        # Run iPSR algorithm
        print("Launching iPSR algorithm in a separate process...")
        process = subprocess.run(["ipsr.exe", "--in", "tmp_ipsr_input.ply", "--out", "tmp_ipsr_output.ply", "--depth", "8", "--iters", "25", "--pointWeight", "6", "--neighbors", "20"])
        print("running...")
        print("Process returned:", process.returncode)
        
        # Read the output, and move it back to the original position, then save
        print("Preparing the output...")    
        mesh = o3d.io.read_triangle_mesh("tmp_ipsr_output.ply")
        mesh.translate(center)
        output_file = os.path.join( output_path, output_filename )
        o3d.io.write_triangle_mesh(output_file, mesh)
        
        # Delete the temporary files
        print("Cleaning up...")
        os.remove("tmp_ipsr_input.ply")
        os.remove("tmp_ipsr_output.ply")
    
    print("Done.")
    return
    
    
    
if __name__ == '__main__':
    main()
