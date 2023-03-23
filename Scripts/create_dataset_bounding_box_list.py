import sys
import numpy as np
import open3d as o3d
import os
import laspy
import pyproj

"""
Read all .las files in the data_path, get the bounding boxes of their data, and list them in the output file
"""

data_path = "S:/Sendai/MMS_20220819/las/"
output_file = "S:/Sendai/MMS_20220819/las_bounds.txt"


def main():
    output_data = process_dataset()
    write_output(output_data)
    print("Done")
    
    
def process_dataset():
    output_data = []
    for root, dirs, files in os.walk( data_path ):
        for filename in files:
            if filename.endswith(".las"):
                print("Reading file: %s..." % filename )
                complete_filename = os.path.join(data_path, filename)
                las_file = laspy.read( complete_filename )
                xyz = np.vstack([las_file.x, las_file.y, las_file.z]).transpose()
                
                all_x = xyz[:,0]
                all_y = xyz[:,1]
                all_z = xyz[:,2]
                x_min = np.min(all_x)
                y_min = np.min(all_y)
                z_min = np.min(all_z)
                x_max = np.max(all_x)
                y_max = np.max(all_y)
                z_max = np.max(all_z)
                print("    Minimum coordinates: (%f,%f,%f)" % (x_min, y_min, z_min) )
                print("    Maximum coordinates: (%f,%f,%f)" % (x_max, y_max, z_max) )
                new_data = {
                    'filename': filename,
                    'min_coord': [x_min, y_min, z_min],
                    'max_coord': [x_max, y_max, z_max]
                }
                output_data.append(new_data)
            else:
                print("Skipping file %s..." % filename )
    return output_data
    

def write_output(data):
    with open(output_file, 'w') as f:
        for i in range(0, len(data)):
            las_name = data[i]['filename']
            min_coord = data[i]['min_coord']
            max_coord = data[i]['max_coord']
            f.write( las_name + " " )
            f.write( str(min_coord[0]) + " " + str(min_coord[1]) + " " + str(min_coord[2]) + " " )
            f.write( str(max_coord[0]) + " " + str(max_coord[1]) + " " + str(max_coord[2]) )
            f.write( "\n" )
            

if __name__ == '__main__':
    main()
