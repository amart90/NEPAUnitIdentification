"""
Tool:               <NEPA Unit determination>
Source Name:        <UnitDetermination_Clip>
Version:            <v1.0, ArcGIS Pro 2.8 and ArcMap 10.7>
Author:             <Anthony Martinez>
Usage:              <Input project area and necessary datasets to output clipped datasets.>
Required Arguments: <parameter0 = projectArea = Project area (feature layer)>
                    <parameter1 = outPath = Output location (workspace)>
Optional Arguments: <parameter2 = clipLandtype = Land type (feature layer)>
                    <parameter3 = clipRiperian = Riperian buffer(feature layer)>
                    <parameter4 = clipMgmtArea = Management Area (feature layer)>
                    <parameter5 = clipSpecialUse = Special use areas (feature layer)>
                    <parameter6 = clipVegPoly = FSVeg stands (feature layer)>
                    <parameter7 = clipOldGrowth = Old Growth (table)>
                    <parameter8 = clipHarvest = Past harvests in FACTS (feature layer)>
                    <parameter9 = clipCHM = Canopy height model (raster layer)>
Description:        <Clips layers needed to identify harvest locations to a project area.>
"""

import arcpy
import os.path
arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True

def ScriptTool(projectArea, outPath, clipLandtype, clipRiperian, clipMgmtArea, clipSpecialUse, clipVegPoly, clipOldGrowth, clipHarvest, clipCHM):
    """ScriptTool function docstring"""

    arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(26911) #NAD_1983_UTM_Zone_11N

   
    # Clip features
    fcs = ["clipLandtype", "clipRiperian", "clipMgmtArea", "clipSpecialUse", "clipHarvest"]
    for fc in fcs:
        if arcpy.Exists(eval(fc)):
            name = fc
            feature = eval(fc)
            if outPath[-4:] == ".gdb":
                out = os.path.join(outPath, name)
            else:
                out = os.path.join(outPath, name) + ".shp"
            arcpy.AddMessage("Clipping " + name + "...")
            arcpy.analysis.Clip(in_features = feature, clip_features = projectArea, out_feature_class = out)

            arcpy.AddMessage("Complete")

    # Add old growth to stands
    fcs = ["clipVegPoly"]
    for fc in fcs:
        if arcpy.Exists(eval(fc)):
            name = fc
            feature = eval(fc)
            if outPath[-4:] == ".gdb":
                out = os.path.join(outPath, name)
            else:
                out = os.path.join(outPath, name) + ".shp"
            arcpy.AddMessage("Clipping " + name + "...")
            with arcpy.EnvManager(outputCoordinateSystem = arcpy.SpatialReference(26911)):
                arcpy.analysis.Clip(in_features = feature, clip_features = projectArea, out_feature_class = out)
            if arcpy.Exists(clipOldGrowth):
                joinFields = ["OLD_GROWTH_STATUS", "OLD_GROWTH_STATUS_METHOD", "OLD_GROWTH_STATUS_YEAR"] 
                arcpy.management.JoinField(in_data = out, in_field = "SETTING_ID", join_table = clipOldGrowth, join_field = "FSVEG_SETTING_ID", fields = joinFields)
            arcpy.AddMessage("Complete")

    # Extract rasters
    if clipCHM:
        rasters = ["clipCHM"]
        for ras in rasters:
            name = ras
            raster = eval(ras)
            out = os.path.join(outPath, name)
            if outPath[-4:] != ".gdb":
                out = out + ".tif"
            arcpy.AddMessage("Clipping " + name + "...")
            outExtractByMask = arcpy.sa.ExtractByMask(in_raster = raster, in_mask_data = projectArea)
            arcpy.management.CopyRaster(outExtractByMask, out)
            #outExtractByMask.save(out)
            arcpy.AddMessage("Complete")

if __name__ == '__main__':
    # ScriptTool parameters
    parameter0 = projectArea = arcpy.GetParameterAsText(0)
    parameter1 = outPath = arcpy.GetParameterAsText(1)
    parameter2 = clipLandtype = arcpy.GetParameterAsText(2)
    parameter3 = clipRiperian = arcpy.GetParameterAsText(3)
    parameter4 = clipMgmtArea = arcpy.GetParameterAsText(4)
    parameter5 = clipSpecialUse = arcpy.GetParameterAsText(5)
    parameter6 = clipVegPoly = arcpy.GetParameterAsText(6)
    parameter7 = clipOldGrowth = arcpy.GetParameterAsText(7)
    parameter8 = clipHarvest = arcpy.GetParameterAsText(8)
    parameter9 = clipCHM = arcpy.GetParameterAsText(9)
    
    ScriptTool(parameter0, parameter1, parameter2, parameter3, parameter4, parameter5, parameter6, parameter7, parameter8, parameter9)




