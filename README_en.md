# LiDAR-data-processing-pipeline
This repository contains scripts for 
- Extracting buildings from LiDAR dataset (assumed already segmented and only containing building data, stored in v1.4 LAS files) with the help of existing LOD2 models (in Wavefront .OBJ format, matching the coordinate system in the LiDAR dataset),
- Aligning and combining building data from multiple point clouds,
- Patching holes in the LiDAR data with points sampled from the LOD2 model,
- Generating meshes using an external tool (iPSR, executable included),
- Detecting windows in the buildings.
  - Note: the window detection algorithms are work on progress, and require a lot of parameter tuning, depending on the targetted data.

This repository **does not** contain the point cloud semantic segmentation AI model or any of the scripts needed for running it.

## Test data
Test data is provided in the form of a set of LAS files, which all contain data for a building used for testing (building_349). The test data needs to be extracted from a zip package that is located in the folder "Data/Test_segmented_data/".

The scripts require LOD2 objects for the target buildings. A single LOD2 model for the test building is included in the folder "Data/LOD2/". It was created by extracting buildings from a LOD2 model of the Sendai center, and has the building in its correct world position so that LiDAR data can be directly compared with it.

## Requirements
(The scripts were developed on a Windows 10 PC, and might require some modifications to run on other platforms.)
- Python 3.8
- The iPSR algorithm used for mesh generation is included as a Windows executable. [It needs to be recompiled for other platforms.](https://github.com/houfei0801/ipsr)
- [Open3D (0.16+)](http://www.open3d.org/docs/release/getting_started.html)
- [Laspy (2.2.0)](https://pypi.org/project/laspy/)
- [Trimesh (3.15.5)](https://trimsh.org/install.html)
- [Matplotlib (3.6.1)](https://pypi.org/project/matplotlib/)
- [Shapely (1.8.5)](https://pypi.org/project/shapely/)

## Detailed usage instructions
The included instructions PDF file contains instructions on how to setup each script, more information on the input data requirements, as well as visualizations of each script's outputs.

## Create building footprints
After modifying the input and output parameters in the script, create 0-dilation 2D footprint polygons for each LOD2 building model:
```sh
python Scripts/01_create_footprint_polygons.py
```
![image](/Docs/Media/01_create_footprint_polygons_output.png)

## Expand footprint polygons
Modify the input and output parameters in the script, and then run it to expand the 0-dilation footprint polygons created in the previous step. This is required in order to deal with any inaccuracies and differencies between reality and the LOD2 models. A 2-meter dilation is generally enough.
```sh
python Scripts/02_polygon_expansion.py
```
![image](/Docs/Media/02_polygon_expansion_output.png)

## Extract buildings and align data
Using the expanded building footprint data created above, the actual LiDAR data is cropped from the point cloud dataset, overlaid and aligned, using the next script:
```sh
python Scripts/04_split_dataset_into_buildings_with_realignment.py
```
The test data provided has already been segmented and filtered to contain mostly building points, which gets rid of any extra elements from around the building included by the dilated footprint polygons.
![image](/Docs/Media/04_Combine_LOD2_and_point_cloud_output.png)


## Combine LiDAR data with LOD2 data
As the LiDAR data does not cover the entire building (even with scan coverage from every side, the bottom and rooftops are still missing), LOD2 data is used to fill in the gaps with a rough estimate of the building's shape. This is required later for mesh generation.
```sh
python Scripts/05_combine_LOD2_and_point_cloud.py
```
![image](/Docs/Media/combine_LiDAR_and_LOD2.png)


## Window detection
The script above, '05_combine_LOD2_and_point_cloud.py', can also be configured to perform window detection on the data. The algorithm first performs Poisson Surface Reconstruction on the combined LiDAR/LOD2 data (resulting in an inferior mesh compared to iPSR), and uses that mesh to detect window positions, outputting them into a separate mesh of window bounding boxes. See the instructions PDF file for how to configure the script for this.

## Create a mesh using iPSR algorithm
A Python script is used to launch the included executable, which computes a mesh for the combined point cloud created above.
```sh
python Scripts/06_run_iPSR.py
```
![image](/Docs/Media/05_run_iPSR_output.png)
