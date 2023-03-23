#import sys
#import numpy as np
import pyproj

"""
4326 - Latitude/longitude - EPSG code for WGS 84/WGS84/World Geodetic System 1984, used in GPS 
6698 - EPSG code for JGD2000 to JGD2011 - Honshu
6713 - ESRI code for JGD2000 to JGD2011 - Northern Honshu affected by the 2011 earthquake
6678 - EPSG code for JGD2011 X10, used in Sendai
"""

input_type       = "latlon" # 'latlon' or 'epsg'
output_type      = "epsg" # 'latlon' or 'epsg'
input_epsg_code  = 4326
output_epsg_code = 6678
input_lat        = 38.258862 # if 'input_type' is 'latlon'
input_lon        = 140.876744
input_x          = 4041.88 # if 'input_type' is 'epsg' 
input_y          = -193061.70
input_z          = 40.0



def main():
    if input_type == "epsg":
        if output_type == "latlon":
            input_epsg_code = 6678
            output_epsg_code = 4326
            lat, lon = crs_to_latlon(input_x, input_y, input_z)
            print("Latitude: %f \nLongitude: %f" % (lat, lon) )
        elif output_type == "epsg":
            # Add transformation if needed...
            pass
    elif input_type == "latlon":
        if output_type == "epsg":
            input_epsg_code = 4326
            output_epsg_code = 6678
            x, y, z = latlon_to_crs(input_lat, input_lon)
            print("X: %f \nY: %f" % (x, y) )


def crs_to_latlon(x,y,z):
    proj = pyproj.Transformer.from_crs(crs_from=input_epsg_code,
                                       crs_to=output_epsg_code, 
                                       always_xy=True)
    longitude, latitude = proj.transform(x, y)
    return latitude, longitude


def latlon_to_crs(latitude, longitude):
    project = pyproj.Transformer.from_crs(crs_from=input_epsg_code, 
                                          crs_to=output_epsg_code, 
                                          always_xy=True)
    x2, y2 = project.transform(longitude, latitude)
    return x2, y2, 0


if __name__ == '__main__':
    main()
