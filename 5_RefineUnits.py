"""
Tool:               <NEPA Unit determination>
Source Name:        <4_UnitDetermination>
Version:            <v1.0, ArcGIS Pro 2.8 and ArcMap 10.7>
Author:             <Anthony Martinez>
Usage:              <Input project area and necessary datasets to output clipped datasets.>
Required Arguments: <parameter0 = projectArea = Project area (feature layer)>
                    <parameter1 = outPath = Output location (workspace)>
                    <parameter2 = clipVegPoly = FSVeg stands (feature layer)>
                    <parameter3 = PreliminaryRegenExclusions = Exclusion from regen units(feature layer)>
                    <parameter4 = PreliminaryCtExclusions = Exclusion from CT units (feature layer)>
                    <parameter5 = sliverSize = Minimum unit size (feature layer)>
                    <parameter5 = standSplit = Minimum unit size (feature layer)>
                    <parameter6 = standSplit = Split units by FSVeg Spatial stands (boolean)>
Description:        <Uses clipped datasets to identify potential timber harvest units>
"""

import arcpy
import os.path
from arcpy import env
arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True

def ScriptTool(projectArea, outPath, clipVegPoly, PreliminaryRegenExclusions, PreliminaryCtExclusions, sliverSize, standSplit):
    """ScriptTool function docstring"""

    # Load files
    outReExcl = os.path.join(outPath, "RefinedRegenExclusions")
    arcpy.CopyFeatures_management(PreliminaryRegenExclusions, outReExcl)
    
    # REGEN: Merge exclusion layers
    # Erase exclusions from the project area
    outErase = r'in_memory\Erase'
    arcpy.analysis.Erase(in_features = projectArea, erase_features = PreliminaryRegenExclusions, out_feature_class = outErase)

    # Remove all < 2 acre slivers
    ## (This method ensures that slivers adjacent to larger units are preserved)

    ## Split into singlepart polygons
    arcpy.management.MultipartToSinglepart(in_features = outErase, out_feature_class = r'in_memory\Split')

    ## Remove all < 2 acre slivers (or as specified)
    sliverQuery = " POLY_AREA > " + str(sliverSize) + " "
    arcpy.AddGeometryAttributes_management(Input_Features = r'in_memory\Split', Geometry_Properties = "AREA", Area_Unit = "ACRES")
    arcpy.MakeFeatureLayer_management(r'in_memory\Split', "units")
    arcpy.SelectLayerByAttribute_management("units", "NEW_SELECTION", sliverQuery)
    outIdentity = r'in_memory\Identity'

    ## Combine/split polygons by adjacency or by stand
    if standSplit.lower() == 'true':
        ### Combine all into one multipart polygon
        arcpy.management.Dissolve(in_features = "units", out_feature_class = r'in_memory\Acre')

        ### Split by FSVeg stands
        arcpy.analysis.Identity(in_features = r'in_memory\Acre', identity_features = clipVegPoly, out_feature_class = outIdentity)
    else:
        ### Combine adjecent units
        arcpy.cartography.AggregatePolygons("units", outIdentity, "5 Meters")

    ## Delete unnecessary fields
    fields_to_delete = [field.name for field in arcpy.ListFields(outIdentity) if not field.required]
    if standSplit.lower() == 'true':
        fields_to_delete.remove("SETTING_ID")
    if fields_to_delete:
        arcpy.DeleteField_management(outIdentity, fields_to_delete)

    # Add Acres field
    arcpy.AddGeometryAttributes_management(Input_Features = outIdentity, Geometry_Properties = "AREA", Area_Unit = "ACRES")
    arcpy.management.AlterField(in_table = outIdentity, field = "POLY_AREA", new_field_name = "Acres")

    outUnits_regen = os.path.join(outPath, "RefinedRegenUnits")
    arcpy.CopyFeatures_management(outIdentity, outUnits_regen)

    # Commercial thin: Merge exclusion layers
    ctExcl =  r'in_memory\ctExcl'
    arcpy.MakeFeatureLayer_management(PreliminaryCtExclusions, ctExcl)
    arcpy.SelectLayerByAttribute_management(ctExcl, "NEW_SELECTION", " Exclusion <> 'Regen harvest unit' ")

        
    if arcpy.Exists(outUnits_regen):
        # Add and populate Exclusion field
        arcpy.management.AddField(in_table = outUnits_regen, field_name = "Exclusion", field_type = "TEXT", field_length = 30)
        arcpy.management.CalculateField(in_table = outUnits_regen, field = "Exclusion", expression = "\"Regen harvest unit\"")
        
        ## Use the ListFeatureClasses function to return a list
        
        env.workspace = outPath
        exclList_ct = [ctExcl, outUnits_regen]
        outExclusions = os.path.join(outPath, "RefinedCtExclusions")

    arcpy.management.Merge(inputs = exclList_ct, output = outExclusions)

    # Erase exclusions from the project area
    outErase = r'in_memory\Erase'
    arcpy.analysis.Erase(in_features = projectArea, erase_features = outExclusions, out_feature_class = outErase)

    # Remove all < 2 acre slivers
    ## (This method ensures that slivers adjacent to larger units are preserved)

    ## Split into singlepart polygons
    arcpy.management.MultipartToSinglepart(in_features = outErase, out_feature_class = r'in_memory\Split')

    ## Remove all < 2 acre slivers (or as spcified)
    arcpy.AddGeometryAttributes_management(Input_Features = r'in_memory\Split', Geometry_Properties = "AREA", Area_Unit = "ACRES")
    arcpy.MakeFeatureLayer_management(r'in_memory\Split', "units")
    arcpy.SelectLayerByAttribute_management("units", "NEW_SELECTION", sliverQuery)
    outIdentity = r'in_memory\Identity'
    
    ## Combine/split polygons by adjacency or by stand
    if standSplit.lower() == 'true':
        ### Combine all into one multipart polygon
        arcpy.management.Dissolve(in_features = "units", out_feature_class = r'in_memory\Acre')

        ### Split by FSVeg stands
        arcpy.analysis.Identity(in_features = r'in_memory\Acre', identity_features = clipVegPoly, out_feature_class = outIdentity)
    else:
        ### Combine adjecent units
        arcpy.cartography.AggregatePolygons("units", outIdentity, "5 Meters")

    ## Delete unnecessary fields
    fields_to_delete = [field.name for field in arcpy.ListFields(outIdentity) if not field.required]
    if standSplit.lower() == 'true':
        fields_to_delete.remove("SETTING_ID")
    if fields_to_delete:
        arcpy.DeleteField_management(outIdentity, fields_to_delete)

    # Add Acres field
    arcpy.AddGeometryAttributes_management(Input_Features = outIdentity, Geometry_Properties = "AREA", Area_Unit = "ACRES")
    arcpy.management.AlterField(in_table = outIdentity, field = "POLY_AREA", new_field_name = "Acres")

    outUnits_ct = os.path.join(outPath, "RefinedCtUnits")
    arcpy.CopyFeatures_management(outIdentity, outUnits_ct)

if __name__ == '__main__':
    # ScriptTool parameters
    parameter0 = projectArea = arcpy.GetParameterAsText(0)
    parameter1 = outPath = arcpy.GetParameterAsText(1)
    parameter2 = clipVegPoly = arcpy.GetParameterAsText(2)
    parameter3 = PreliminaryRegenExclusions = arcpy.GetParameterAsText(3)
    parameter4 = PreliminaryCtExclusions = arcpy.GetParameterAsText(4)
    parameter5 = sliverSize = arcpy.GetParameterAsText(5)
    parameter6 = standSplit = arcpy.GetParameterAsText(6)


    ScriptTool(parameter0, parameter1, parameter2, parameter3, parameter4, parameter5, parameter6)
