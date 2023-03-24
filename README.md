# LiDAR-data-processing-pipeline
Scripts for extracting buildings from LiDAR dataset (assumed already segmented) using existing LOD2 models, aligning and combining them, and creating meshes.

## Initial setup
Test data is provided in the form of a set of LAS files, which all contain data for a building used for testing (building_349). The test data needs to be extracted from a zip package that is located in the folder "Data/Test_segmented_data/".

The scripts require LOD2 objects for the target buildings. A single LOD2 model for the test building is included in the folder "Data/LOD2/". It was created by extracting buildings from a LOD2 model of the Sendai center, and has the building in its correct world position so that LiDAR data can be directly compared with it.

The scripts were developed on a Windows 10 PC, and might require some modifications to run on other platforms. The iPSR algorithm used for iterative mesh generation (https://github.com/houfei0801/ipsr) is included as a Windows executable, and needs to be recompiled for other platforms.

More detailed instructions and images of the script outputs can be found in the included instructions.pdf file.

## Create building footprints
After modifying the input and output parameters in the script, create 0-dilation 2D footprint polygons for each LOD2 building model:
```sh
python Scripts/01_create_footprint_polygons.py
```

## Expand footprint polygons
Modify the input and output parameters in the script, and then run it to expand the 0-dilation footprint polygons created in the previous step. This is required in order to deal with any inaccuracies and differencies between reality and the LOD2 models. A 2-meter dilation is generally enough.
```sh
python Scripts/02_polygon_expansion.py
```

## Extract buildings and align data
Using the expanded building footprint data created above, the actual LiDAR data is cropped from the point cloud dataset, overlaid and aligned, using the next script:
```sh
python Scripts/04_split_dataset_into_buildings_with_realignment.py
```
The test data provided has already been segmented and filtered to contain mostly building points, which gets rid of any extra elements from around the building included by the dilated footprint polygons.

## Combine LiDAR data with LOD2 data
As the LiDAR data does not cover the entire building (even with scan coverage from every side, the bottom and rooftops are still missing), LOD2 data is used to fill in the gaps with a rough estimate of the building's shape. This is required later for mesh generation.
```sh
python Scripts/05_combined_LOD2_and_point_cloud.py
```

## Create a mesh using iPSR algorithm
A Python script is used to launch the included executable, which computes a mesh for the combined point cloud created above.
```sh
python Scripts/06_run_iPSR.py
```
