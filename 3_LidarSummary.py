"""
Tool:               <Lidar Summary>
Source Name:        <3_LidarSummary>
Version:            <v1.0, ArcGIS Pro 2.8 and ArcMap 10.7>
Author:             <Anthony Martinez>
Required Arguments: <parameter0 = treeTop = TreTop height points (feature layer)>
                    <parameter1 = clipVegPoly = FSVeg stad polygons (feature layer)>
                    <parameter2 = outPath = Output location (workspace)>
                    <parameter3 = ctMin = Output location (workspace)>
                    <parameter4 = ctMax = Output location (workspace)>
                    <parameter5 = regenMin = Output location (workspace)>
                    <parameter6 = regenMax = Output location (workspace)>
Description:        <Compute tree height summary statistics (minimum, maximum, mean, mediad) for each stand>
"""

import arcpy
import os.path
arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True

def ScriptTool(treeTop, clipVegPoly, outPath, ctMin, ctMax, regenMin, regenMax):
    """ScriptTool function docstring"""
    arcpy.AddMessage("Getting all set up...")

    # Remove unnecessary fields from VegPoly
    stands = "in_memory/stands"
    arcpy.CopyFeatures_management(clipVegPoly, stands) 
    fields_to_delete = [field.name for field in arcpy.ListFields(stands) if not field.required]
    fields_to_delete.remove("SETTING_ID")
    arcpy.DeleteField_management(stands, fields_to_delete)

    # Add summary fields to VegPoly
    arcpy.AddGeometryAttributes_management(stands, Geometry_Properties = "AREA", Area_Unit = "ACRES")
    arcpy.management.AlterField(stands, "POLY_AREA", new_field_name = "Acres")
    arcpy.management.AddField(stands, "Regen_Count", "SHORT")
    arcpy.management.AddField(stands, "Regen_TPA", "DOUBLE")
    arcpy.management.AddField(stands, "CT_Count", "SHORT")
    arcpy.management.AddField(stands, "CT_TPA", "DOUBLE")

    # Define queries for CT and regen height thresholds
    ctQuery = " Height >= " + str(ctMin)
    if 'ctMax' in locals():
        ctQuery = ctQuery + " AND Height <= " + str(ctMax)
    regenQuery = " Height >= " + str(regenMin)
    if regenMax <> "":
        regenQuery = regenQuery + " AND Height <= " + str(regenMax)

    # Make temporary layers from the feature class
    arcpy.MakeFeatureLayer_management(treeTop, "regen")
    arcpy.MakeFeatureLayer_management(treeTop, "ct")

    # Select trees of within height thresholds
    arcpy.SelectLayerByAttribute_management("regen", "NEW_SELECTION", regenQuery)
    arcpy.SelectLayerByAttribute_management("ct", "NEW_SELECTION", ctQuery)


    # Define variables for couting function
    expression = "recalc(!FREQUENCY!)"
    codeblock = """def recalc(freq):
        if freq > -1:
            return freq
        else:
            return 0"""

    # Count regen height trees within each stand
    arcpy.AddMessage("Counting regen harvest sized trees...")
    arcpy.SpatialJoin_analysis("regen", stands, "in_memory/PointsInPolys")
    arcpy.Statistics_analysis ("in_memory/PointsInPolys", "in_memory/SS_PointsInPolys", [["SETTING_ID", "Count"]], "SETTING_ID")
    arcpy.JoinField_management(stands, "SETTING_ID", "in_memory/SS_PointsInPolys", "SETTING_ID", "FREQUENCY")
    arcpy.CalculateField_management(stands, "Regen_Count", expression, "PYTHON", codeblock)
    arcpy.DeleteField_management(stands, "FREQUENCY")

    # Count commercial thin height trees within each stand
    arcpy.AddMessage("Counting commercial thin sized trees...")
    arcpy.SpatialJoin_analysis("ct", stands, "in_memory/PointsInPolys")
    arcpy.Statistics_analysis ("in_memory/PointsInPolys", "in_memory/SS_PointsInPolys", [["SETTING_ID", "Count"]], "SETTING_ID")
    arcpy.JoinField_management(stands, "SETTING_ID", "in_memory/SS_PointsInPolys", "SETTING_ID", "FREQUENCY")
    arcpy.CalculateField_management(stands, "CT_Count", expression, "PYTHON", codeblock)
    arcpy.DeleteField_management(stands, "FREQUENCY")

    # Calculate TPA
    arcpy.AddMessage("Calculating Trees per Acre")
    arcpy.management.CalculateField(in_table = stands, field = "Regen_TPA", expression = "round(!Regen_Count! / !Acres!, 2)", expression_type = "PYTHON") # should be changed to PYTHON3 if using ArcGIS Pro
    arcpy.management.CalculateField(in_table = stands, field = "CT_TPA", expression = "round(!CT_Count! / !Acres!, 2)", expression_type = "PYTHON")

    # Summarize tree heights by stand (Mean/Min/Max Ht)
    # This code comes from Ian Broad (2015), www.ianbroad.com
    mem_polygon = arcpy.CopyFeatures_management(stands, "in_memory/treeTopSummary")

    arcpy.AddField_management(mem_polygon, "MinHeight", "DOUBLE")
    arcpy.AddField_management(mem_polygon, "MaxHeight", "DOUBLE")
    arcpy.AddField_management(mem_polygon, "MeanHeight", "DOUBLE")
    arcpy.AddField_management(mem_polygon, "MedianHeight", "DOUBLE")

    result = arcpy.GetCount_management(stands)
    features = int(result.getOutput(0))

    def median(lst):
        n = len(lst)
        s = sorted(lst)
        return (s[n//2-1]/2.0+s[n//2]/2.0, s[n//2])[n % 2] if n else None

    arcpy.AddMessage("Calclating height statistics for each stand...")
    arcpy.SetProgressor("step", "Calculating Point Statistics...", 0, features, 1)

    with arcpy.da.UpdateCursor(mem_polygon, ("SHAPE@", "MinHeight", "MaxHeight", "MeanHeight", "MedianHeight")) as polygon_update:
        for poly_row in polygon_update:
            try:
                point_values = []
                mem_point = arcpy.MakeFeatureLayer_management(treeTop, "mem_points")
                arcpy.SelectLayerByLocation_management(mem_point, "COMPLETELY_WITHIN", poly_row[0])

                with arcpy.da.SearchCursor(mem_point, ("Height")) as point_search:
                    for point_row in point_search:
                        if point_row[0] is not None and point_row[0] != "":
                            point_values.append(float(point_row[0]))

                poly_row[1] = float(round(min(point_values), 2))
                poly_row[2] = float(round(max(point_values), 2))
                poly_row[3] = float(round(sum(point_values)/float(len(point_values)), 2))
                poly_row[4] = float(round(median(point_values), 2))

                polygon_update.updateRow(poly_row)

                arcpy.SetProgressorPosition()

            except Exception as e:
                arcpy.AddMessage(str(e.message))

    # Write output file
    arcpy.AddMessage("Writing output file..")
    outSummary = os.path.join(outPath, "LidarSummary")
    arcpy.CopyFeatures_management(mem_polygon, outSummary)


if __name__ == '__main__':
    # ScriptTool parameters
    parameter0 = treeTop = arcpy.GetParameterAsText(0)
    parameter1 = clipVegPoly = arcpy.GetParameterAsText(1)
    parameter2 = outPath = arcpy.GetParameterAsText(2)
    parameter3 = ctMin = arcpy.GetParameterAsText(3)
    parameter4 = ctMax = arcpy.GetParameterAsText(4)
    parameter5 = regenMin = arcpy.GetParameterAsText(5)
    parameter6 = regenMax = arcpy.GetParameterAsText(6)

    
    ScriptTool(parameter0, parameter1, parameter2, parameter3, parameter4, parameter5, parameter6)

