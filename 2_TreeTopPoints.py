"""
Tool:               <Lidar tree top and canopy segmentation>
Source Name:        <PointAndSeg>
Version:            <v1.0, ArcGIS Pro 2.8 and ArcMap 10.7>
Author:             <Anthony Martinez>
Usage:              <Input canopy height raster and project area (and adjust option parameters) to output point layer with location and heights of tree tops.>
Required Arguments: <parameter0 = Canopy height model (raster layer)>
                    <parameter1 = Clipping feature (feature layer)>
                    <parameter4 = Minimum tree height in feet(double)>
                    <parameter5 = Output workspace (workspace)>
Optional Arguments: <parameter2 = Canopy height model smoothing switch (boolean)>
                    <parameter3 = Convert canopy heights from m to ft (boolean)>
Description:        <Detects and computes the location and height of individual trees within the LiDAR-derived Canopy Height Model (CHM).
                     The algorithm implemented in this function is local maximum with a fixed window size.
                     Adapted from FindTreeCHM tool from "rLiDAR" R package:
                         Carlos Alberto Silva, Nicholas L. Crookston, Andrew T. Hudak, Lee A. Vierling, Carine Klauberg, Adrian Cardil and Caio Hamamura (2021).
                         rLiDAR: LiDAR Data Processing and Visualization.
                         R package version 0.1.5. https://CRAN.R-project.org/package=rLiDAR>
"""
import arcpy
import os.path

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True


def ScriptTool(parameter0, parameter1, parameter2, parameter3, parameter4, parameter5):
    """ScriptTool function docstring"""
    # Load Canopy height model
    arcpy.AddMessage("(0/6) Clipping canopy height model")
    CHM_Ext = arcpy.sa.ExtractByMask(in_raster = parameter0, in_mask_data = parameter1)
    arcpy.AddMessage("(1/6) Clipped canopy height model")
    
    # Smooth CHM if desired
    if parameter2.lower() == 'true':
        CHM_Sm = arcpy.sa.FocalStatistics(in_raster=CHM_Ext, neighborhood= "Rectangle 3 3 CELL", statistics_type= "Mean", ignore_nodata="DATA", percentile_value=90)
        arcpy.AddMessage("(2/6) Smoothed canopy height model")
    else:
        CHM_Sm = CHM_Ext
        arcpy.AddMessage("(2/6) Skipped canopy smoothing")
    
    # Convert CHM to feet if necessary
    if parameter3.lower() == 'true':
        CHM_Ft = CHM_Sm * 3.281
        arcpy.AddMessage("(3/6) Converted canopy heights from m to ft")
    else:
        CHM_Ft = CHM_Sm
        arcpy.AddMessage("(3/6) Skipped canopy height unit conversion")
    
    # Set minimum tree height 
    CHM_MinHt = arcpy.sa.SetNull(CHM_Ft, CHM_Ft, "VALUE < " + parameter4)
    arcpy.AddMessage("(4/6) Set minimum tree height")
    
    # Calculate local maxima
    CHM_LocalMax = arcpy.sa.FocalStatistics(in_raster = CHM_MinHt, neighborhood = "Rectangle 5 5 CELL", statistics_type = "MAXIMUM", ignore_nodata = "DATA", percentile_value = 90)
    
    # Local maximum = CHM
    treeLoc = arcpy.sa.EqualTo(in_raster_or_constant1 = CHM_LocalMax, in_raster_or_constant2 = CHM_MinHt)
    
    # Isolate tree tops
    treeLocHt = arcpy.sa.SetNull(in_conditional_raster = treeLoc, in_false_raster_or_constant = CHM_MinHt, where_clause = "Value = 0")
    
    # Raster to point
    treeTop = arcpy.conversion.RasterToPoint(in_raster = treeLocHt, out_point_features = "treeTop", raster_field = "Value")
    arcpy.AddMessage("(5/6) Identified tree tops")

    # Rename tree top columns
    treeTop = arcpy.management.AlterField(in_table = treeTop, field = "grid_code", new_field_name = "Height", new_field_alias = "Height (ft)")[0]
    treeTop = arcpy.management.AlterField(in_table = treeTop, field = "pointid", new_field_name = "TreeId", new_field_alias = "TreeId")[0]
    
    # Reclass tree points to ID number
    treeTopReclass = arcpy.sa.ReclassByTable(in_raster = treeLocHt, in_remap_table = treeTop, from_value_field = "Height", to_value_field = "Height", output_value_field = "TreeId", missing_values = "DATA")
    
    # Save tree points, canopy segmentation, and canopy height model to desired output location
    if parameter5[-4:] == ".gdb":
        rasterName = arcpy.ValidateTableName("CHM_ft", parameter5)
        treeTopName = arcpy.ValidateTableName("TreeTop", parameter5)
    else:
        rasterName = arcpy.ValidateTableName("CHM_ft.tif", parameter5)
        treeTopName = arcpy.ValidateTableName("TreeTop.shp", parameter5)

    outRaster = os.path.join(parameter5, rasterName)
    outTreeTop = os.path.join(parameter5, treeTopName)

    arcpy.management.CopyRaster(CHM_Ft, outRaster)
    arcpy.management.CopyFeatures(treeTop, outTreeTop)
    arcpy.AddMessage("(6/6) Saved files to workspace")

if __name__ == '__main__':
    # ScriptTool parameters
    parameter0 = arcpy.GetParameterAsText(0)
    parameter1 = arcpy.GetParameter(1)
    parameter2 = arcpy.GetParameterAsText(2)
    parameter3 = arcpy.GetParameterAsText(3)
    parameter4 = arcpy.GetParameterAsText(4)
    parameter5 = arcpy.GetParameterAsText(5)
    
    ScriptTool(parameter0, parameter1, parameter2, parameter3, parameter4, parameter5)


