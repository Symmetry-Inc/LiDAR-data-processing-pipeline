import matplotlib.path as matplotlibpath

"""
Get all buildings inside a polygon.
Use this script only, if multiple buildings in a defined area need to be extracted.
The polygon should be set in such a way that it contains all target buildings completely, since only a single point of each building is tested for being in the area.
The polygon coordinates can be created by picking latitude/longitude coordinates of the target points, and using the script 'epsg_converter.py' to convert them into the coordinate system used.
"""

footprints_file = "S:/OSS/Data/Footprints/test_footprint_0m_dilation.txt" # 0-dilation polygon is used here.
output_file = "S:/OSS/Data/buildings.txt"
polygon_points = [[3770.369092, -193340.996670],
                  [3785.942776, -193332.554141],
                  [3770.343822, -193286.722423],
                  [3733.767196, -193296.062556]]

def main():
    print("\n\nChecking buildings against the input polygon:")
    print(polygon_points)
    path = matplotlibpath.Path(polygon_points)
    accepted_buildings = []
    checked_num = 0
    with open(footprints_file, 'r') as polygons_file:
        input_data = polygons_file.readlines()
        for line in input_data:
            words = line.split()
            object_name = str(words[0])
            building_name = object_name[0:-4]
            x = float(words[2])
            y = float(words[3])
            building_point = [[x, y]]
            is_inside = path.contains_points(building_point)
            if is_inside[0] == True:
                accepted_buildings.append("\"" + object_name + "\",")
            checked_num += 1
    print( "Checked {num} buildings, found {num2} inside the polygon:".format(num=checked_num, num2=len(accepted_buildings)) )
    print( accepted_buildings )
    print("-->Writing to {filename}".format(filename=output_file))
    
    with open(output_file, 'w') as buildings_file:
        buildings_file.write("[")
        for i in range(len(accepted_buildings)):
            name = accepted_buildings[i]
            name += "\n"
            buildings_file.write(name)
        buildings_file.write("]")    
        
    
    print("Done.")
  

if __name__ == '__main__':
    main()
