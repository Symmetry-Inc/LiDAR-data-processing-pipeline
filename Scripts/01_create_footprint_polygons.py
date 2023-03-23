import os
import matplotlib.pyplot as plt
import numpy as np
from os import listdir
from os.path import isfile, join
import trimesh


"""
Read all Wavefront OBJ files in the input path (each file must contain a single mesh), create a horizontal 2D slice near the bottom of the mesh, and compute the perimeter polygon.
A simple dilation algorithm is included, but it does not consider neighbor buildings. Use 'neighbor_minding_polygon_expansion.py' instead, after creating the 0-dilation polygons with this script.
"""

input_path               = "S:/OSS/Data/LOD2/"
output_filename          = "S:/OSS/Data/Footprints/test_footprint_0m_dilation.txt"
dilation_amount          = 0.0
visualize_results        = True

def main():
                  
    input_files = [f for f in listdir(input_path) if isfile(join(input_path, f)) and f.endswith(".obj")]
    file_number = 0
    output_visualization_x = []
    output_visualization_y = []
    with open(output_filename, 'w') as output_file:
        for filename in input_files:
            
            print("Processing file #{num}: {name}".format(num=file_number, name=filename))
            model_file = os.path.join(input_path, filename)
            mesh = trimesh.load(model_file, process=False, force="mesh", skip_materials=True, skip_texture=True)
            
            # Calculate cross section of the mesh that will represent the building footprint
            slice_2D, to_3D = cross_section(mesh)
            
            # Extract the point values that define the perimeter of the polygon
            poly = slice_2D.polygons_full[0]
            x_coordinates, y_coordinates = poly.exterior.coords.xy
            
            if dilation_amount > 0.0:
                dilated_x, dilated_y = dilate_polygon( x_coordinates, y_coordinates )
            else:
                dilated_x = x_coordinates
                dilated_y = y_coordinates
            
            building_name = filename[:-4]
            polygon_string = filename + " " + building_name + "_points.ply"
            if visualize_results == True:
                vis_data_x = []
                vis_data_y = []
                for i in range(len(dilated_x)):
                    polygon_string += " " + str(dilated_x[i]) + " " + str(dilated_y[i])
                    vis_data_x.append(dilated_x[i])
                    vis_data_y.append(dilated_y[i])
                output_visualization_x.append(np.asarray(vis_data_x))
                output_visualization_y.append(np.asarray(vis_data_y))
            polygon_string += "\n"
            output_file.write(polygon_string)
            file_number += 1

    if visualize_results == True:
        plt.title("Polygons")
        plt.xlabel("X axis")
        plt.ylabel("Y axis")
        for i in range(len(output_visualization_x)):
            plt.plot(output_visualization_x[i], output_visualization_y[i], color="black")
        plt.show()
            

def cross_section(mesh):
    """
    Using just the mesh.section() method together with slice.to_planar() causes the resulting polygon to be centered around origin.
    This way it will retain its world coordinates.
    """
    plane_normal = [0,0,1]
    bounding_box = mesh.bounds
    min_x = bounding_box[0, 0]
    max_x = bounding_box[1, 0]
    min_y = bounding_box[0, 1]
    max_y = bounding_box[1, 1]
    min_z = bounding_box[0, 2]
    max_z = bounding_box[1, 2]
    middle_x = min_x + ((max_x - min_x)/2.0)
    middle_y = min_y + ((max_y - min_y)/2.0)
    cut_height = min_z + 0.6
    
    #print("Min_z: %f, max_z: %f" % (min_z, max_z) )
    mesh_slice = mesh.section(plane_origin=[middle_x, middle_y, cut_height], plane_normal=plane_normal)
    
    # transformation matrix for to_planar.
    to_2D = trimesh.geometry.align_vectors(plane_normal, [0,0,1])
    slice_2D, to_3D = mesh_slice.to_planar(to_2D = to_2D)
    
    return slice_2D, to_3D


def dilate_polygon( x_coordinates, y_coordinates ):
    """
    Traverse the (closed, first and last nodes are the same) polygon defined by the input coordinates, calculate each edge normal, and use them to calculate each node normal. 
    Displace each node along the normal to dilate the polygon.
    For a 2D vector, if dx = x2 - x1 and dy = y2 - y1, then the possible normals are (-dy, dx) and (dy, -dx)
    Cross-product decides, which is the correct one (always stick to the same side of the line, as the polygon is traversed)
    cp = ((x2-x1)(y3-y1))-((y2-y1)(x3-x1)), where (x3, y3) is a point being tested (just add candidate normal to either polygon node coordinates).
    """
    normals = []
    edge_halfway_points = []
    dilated_x = []
    dilated_y = []
            
    # Calculate polygon edge normals. First normal will be between then first and last node of the polygon.    
    for i in range(len(x_coordinates)-1): # Ignoring the last node, which is the same as the first node
        x1 = x_coordinates[i]
        y1 = y_coordinates[i]
        x2 = x_coordinates[i+1]
        y2 = y_coordinates[i+1]
        
        halfway_x = x1 + 0.5*(x2-x1)
        halfway_y = y1 + 0.5*(y2-y1)
        edge_halfway_points.append([halfway_x, halfway_y])
        
        dx = x2 - x1
        dy = y2 - y1
        n1x = -dy
        n1y = dx
        n2x = dy
        n2y = -dx
        test_point_x = halfway_x + n1x
        test_point_y = halfway_y + n1y
        cross_product = ((x2-x1)*(test_point_y-y1))-((y2-y1)*(test_point_x-x1))
        if cross_product < 0:
            chosen_normal = [n1x,n1y]
        elif cross_product == 0:
            # Should never end up here, unless the angle between polygon components is 180 degrees.
            print("Found a 180-degree angle in the footprint polygon!")
            chosen_normal = [n1x, n1y] # Just to avoid an error, should add error handling...
        else:
            chosen_normal = [n2x, n2y]
        normals.append(chosen_normal)
            
    # Calculate normalized vertex normals, and dilate node positions along it by a set amount
    for i in range(len(x_coordinates)-1):
        n1x = normals[i-1][0]
        n1y = normals[i-1][1]
        n2x = normals[i][0]
        n2y = normals[i][1]
        vn = np.array([n1x+n2x, n1y+n2y])
        normalized_vn = vn / np.sqrt(np.sum(vn**2))
        new_x = x_coordinates[i] + normalized_vn[0] * dilation_amount
        new_y = y_coordinates[i] + normalized_vn[1] * dilation_amount
        dilated_x.append(new_x)
        dilated_y.append(new_y)
        
    # Move the final node identically to the first one, since they are the same vertex
    dilated_x.append(dilated_x[0])
    dilated_y.append(dilated_y[0])
        
    return dilated_x, dilated_y
    
    
if __name__ == '__main__':
    main()
