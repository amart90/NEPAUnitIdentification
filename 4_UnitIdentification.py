"""
Tool:               <NEPA Unit determination>
Source Name:        <4_UnitIdentification>
Version:            <v1.0, ArcGIS Pro 2.8 and ArcMap 10.7>
Author:             <Anthony Martinez>
Usage:              <Input project area and necessary datasets to output clipped datasets.>
Required Arguments: <parameter0 = projectArea = Project area (feature layer)>
                    <parameter1 = outPath = Output location (workspace)>
                    <parameter2 = clipVegPoly = FSVeg stands (feature layer)> 
Optional Arguments: <parameter3 = recruitment = Land type (boolean)>
                    <parameter4 = clipRiperian = Riperian buffer(feature layer)>
                    <parameter5 = clipLandtype = Land type (feature layer)>
                    <parameter6 = clipSpecialUse = Special use areas (feature layer)>
                    <parameter7 = clipHarvest = Past harvests in FACTS (feature layer)>
                    <parameter8 = harvestAge = Age of harvests to exclude (integer)>
                    <parameter9 = clipMgmtArea = Management Area (feature layer)>
                    <parameter10 = clipLidarSummary = Lidar Summary from TreeTops and LidarSummary tools (feature layer)>
                    <parameter11 = regenTPA = The minimum TPA of regen sized trees in regen units (short)>
                    <parameter12 = ctTPA = The minimum TPA of CT sized trees in CT units (short)>
                    <parameter13 = sliverSize = Minimum unit size (feature layer)>
                    <parameter14 = standSplit = Split units by FSVeg Spatial stands (boolean)>
Description:        <Uses clipped datasets to identify potential timber harvest units>
"""

import arcpy
import os.path
from arcpy import env
from datetime import date
arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True

def ScriptTool(projectArea, outPath, clipVegPoly, recruitment, clipRiperian, clipLandtype, clipSpecialUse, clipHarvest, harvestAge, clipMgmtArea, clipLidarSummary, regenTPA, ctTPA, sliverSize, standSplit):
    """ScriptTool function docstring"""
    
    # Riperian buffers
    if arcpy.Exists(clipRiperian):
        arcpy.AddMessage("Working on the riperian buffers...")
        # Write the selected features to a new featureclass
        riperian = os.path.join(outPath, "exclRiperianBuffer")
        arcpy.CopyFeatures_management(clipRiperian, riperian)

        # Remove non-required fields
        fields_to_delete = [field.name for field in arcpy.ListFields(riperian) if not field.required]
        for field in fields_to_delete:
            arcpy.DeleteField_management(riperian, field)

        # Add and populate Exclusion field
        arcpy.management.AddField(in_table = riperian, field_name = "Exclusion", field_type = "TEXT", field_length = 30)
        arcpy.management.CalculateField(in_table = riperian, field = "Exclusion", expression = "\"Riperian buffer\"") 
        arcpy.AddMessage("Complete")
        
    # Landtype
    if arcpy.Exists(clipLandtype):
        arcpy.AddMessage("Working on the land type...")
        # Make a layer from the feature class
        arcpy.MakeFeatureLayer_management(clipLandtype, "landtype") 

        # Select mass wasting sites   
        arcpy.SelectLayerByAttribute_management("landtype", "NEW_SELECTION", " DESCRIPTION = 'Mass Wasting Sites' ")

        # Write the selected features to a new featureclass
        massWasting = os.path.join(outPath, "exclMassWasting")
        arcpy.CopyFeatures_management("landtype", massWasting)
        
        # Remove non-required fields
        fields_to_delete = [field.name for field in arcpy.ListFields(massWasting) if not field.required]
        for field in fields_to_delete:
            arcpy.DeleteField_management(massWasting, field)

        # Add and populate Exclusion field
        arcpy.management.AddField(in_table = massWasting, field_name = "Exclusion", field_type = "TEXT", field_length = 30)
        arcpy.management.CalculateField(in_table = massWasting, field = "Exclusion", expression = "\"Mass wasting site\"") 
        arcpy.AddMessage("Complete")
        
    # Special use area
    if arcpy.Exists(clipSpecialUse):
        arcpy.AddMessage("Working on the special use areas...")
        # Write the features to a new featureclass
        specialUse = os.path.join(outPath, "exclSpecialUseArea")
        arcpy.CopyFeatures_management(clipSpecialUse, specialUse)

        # Remove non-required fields
        fields_to_delete = [field.name for field in arcpy.ListFields(specialUse) if not field.required]
        for field in fields_to_delete:
            arcpy.DeleteField_management(specialUse, field)

        # Add and populate Exclusion field
        arcpy.management.AddField(in_table = specialUse, field_name = "Exclusion", field_type = "TEXT", field_length = 30)
        arcpy.management.CalculateField(in_table = specialUse, field = "Exclusion", expression = "\"Special use area\"") 
        arcpy.AddMessage("Complete")
        
    # Harvested areas
    if arcpy.Exists(clipHarvest):
        arcpy.AddMessage("Working on the harvest areas...")
        # Make a layer from the feature class
        arcpy.MakeFeatureLayer_management(clipHarvest, "harvest") 

        # Select Regen harvests within x years
        harvestAge = 80
        year = date.today().year - harvestAge
        harvestSelect = " ACTIVITY_CODE LIKE '41%' AND FY_COMPLETED >= '" + str(year) + "' "
        arcpy.SelectLayerByAttribute_management("harvest", "NEW_SELECTION", harvestSelect)
        
        # Write the selected features to a new featureclass
        harvest = os.path.join(outPath, "exclHarvest")
        arcpy.CopyFeatures_management("harvest", harvest)
        
        # Remove non-required fields
        fields_to_delete = [field.name for field in arcpy.ListFields(harvest) if not field.required]
        for field in fields_to_delete:
            arcpy.DeleteField_management(harvest, field)

        # Add and populate Exclusion field
        arcpy.management.AddField(in_table = harvest, field_name = "Exclusion", field_type = "TEXT", field_length = 30)
        harvestQuery = "\"Regen harvest within " + str(harvestAge) + " yrs\""
        arcpy.management.CalculateField(in_table = harvest, field = "Exclusion", expression = "\"Regen harvest within 80 yrs\"")
        arcpy.AddMessage("Complete")
        
    # Management Areas
    if arcpy.Exists(clipMgmtArea):
        arcpy.AddMessage("Working on the management areas...")
        # Make a layer from the feature class
        arcpy.MakeFeatureLayer_management(clipMgmtArea, "mgmt") 

        # Select unsuitable management areas
        arcpy.SelectLayerByAttribute_management("mgmt", "NEW_SELECTION", " MGTAREA IN ('US', 'B2', 'B1') ")
        
        # Write the selected features to a new featureclass
        mgmt = os.path.join(outPath, "exclMgmtArea")
        arcpy.CopyFeatures_management("mgmt", mgmt)
        
        # Remove non-required fields
        fields_to_delete = [field.name for field in arcpy.ListFields(mgmt) if not field.required]
        for field in fields_to_delete:
            arcpy.DeleteField_management(mgmt, field)

        # Add and populate Exclusion field
        arcpy.management.AddField(in_table = mgmt, field_name = "Exclusion", field_type = "TEXT", field_length = 30)
        arcpy.management.CalculateField(in_table = mgmt, field = "Exclusion", expression = "\"Unsuitable management area\"")
        arcpy.AddMessage("Complete")
        
    # Old growth
    if arcpy.Exists(clipVegPoly):
        #Check of Old Growth Status field exists
        lstFields = [f.name for f in arcpy.ListFields(clipVegPoly)]
        if "OLD_GROWTH_STATUS" in lstFields:
            arcpy.AddMessage("Working on the old growth...")
            # Make a layer from the feature class
            arcpy.MakeFeatureLayer_management(clipVegPoly, "oldgrowth")
        
            # Select retained old growth
            recruitment = "True"
            if recruitment.lower() == 'true':
                arcpy.SelectLayerByAttribute_management("oldgrowth", "NEW_SELECTION", " OLD_GROWTH_STATUS in ('Old Growth', 'Step Down', 'Recruitment') ")
            else:
                arcpy.SelectLayerByAttribute_management("oldgrowth", "NEW_SELECTION", " OLD_GROWTH_STATUS in ('Old Growth', 'Step Down') ")

            # Write the selected features to a new featureclass
            oldGrowth = os.path.join(outPath, "exclOldGrowth")
            arcpy.CopyFeatures_management("oldgrowth", oldGrowth)

            # Remove non-required fields
            fields_to_delete = [field.name for field in arcpy.ListFields(oldGrowth) if not field.required]
            for field in fields_to_delete:
                arcpy.DeleteField_management(oldGrowth, field)

            # Add and populate Exclusion field
            arcpy.management.AddField(in_table = oldGrowth, field_name = "Exclusion", field_type = "TEXT", field_length = 30)
            arcpy.management.CalculateField(in_table = oldGrowth, field = "Exclusion", expression = "\"Old growth\"")
            arcpy.AddMessage("Complete")
            
    # Lidar Summary
    if arcpy.Exists(clipLidarSummary):
        arcpy.AddMessage("Working on the lidar summary...")
        #Regen harvest
        # Make a layer from the feature class
        arcpy.MakeFeatureLayer_management(clipLidarSummary, "Regen") 

        # Select areas with too few regen sized trees
        regenQuery = "Regen_TPA < " + str(regenTPA) 
        arcpy.SelectLayerByAttribute_management("Regen", "NEW_SELECTION", regenQuery)
        
        # Write the selected features to a new featureclass
        regen = os.path.join(outPath, "exclRegenTPA")
        arcpy.CopyFeatures_management("Regen", regen)
        
        # Remove non-required fields
        fields_to_delete = [field.name for field in arcpy.ListFields(regen) if not field.required]
        for field in fields_to_delete:
            arcpy.DeleteField_management(regen, field)

        # Add and populate Exclusion field
        arcpy.management.AddField(in_table = regen, field_name = "Exclusion", field_type = "TEXT", field_length = 30)
        arcpy.management.CalculateField(in_table = regen, field = "Exclusion", expression = "\"Too few regen-sized trees\"")

        # Commercial thin
        # Make a layer from the feature class
        arcpy.MakeFeatureLayer_management(clipLidarSummary, "Ct") 

        # Select areas with too few regen sized trees
        ctQuery = "CT_TPA < " + str(ctTPA) 
        arcpy.SelectLayerByAttribute_management("Ct", "NEW_SELECTION", ctQuery)
        
        # Write the selected features to a new featureclass
        ct = os.path.join(outPath, "exclCtTPA")
        arcpy.CopyFeatures_management("Ct", ct)
        
        # Remove non-required fields
        fields_to_delete = [field.name for field in arcpy.ListFields(ct) if not field.required]
        for field in fields_to_delete:
            arcpy.DeleteField_management(ct, field)

        # Add and populate Exclusion field
        arcpy.management.AddField(in_table = ct, field_name = "Exclusion", field_type = "TEXT", field_length = 30)
        arcpy.management.CalculateField(in_table = ct, field = "Exclusion", expression = "\"Too few comm thin-sized trees\"")
        arcpy.AddMessage("Complete")
            
    # REGEN: Merge exclusion layers
    ## Use the ListFeatureClasses function to return a list
    arcpy.AddMessage("Building regeneration harvest units...")
    env.workspace = outPath
    exclList_regen = arcpy.ListFeatureClasses(wild_card = "excl*")
    if "exclCtTPA" in exclList_regen:
        exclList_regen.remove("exclCtTPA")
    outExclusions = os.path.join(outPath, "PreliminaryRegenExclusions")

    arcpy.management.Merge(inputs = exclList_regen, output = outExclusions)

    ## Erase exclusions from the project area
    outErase = r'in_memory\Erase'
    arcpy.analysis.Erase(in_features = projectArea, erase_features = outExclusions, out_feature_class = outErase)

    ## Remove all < 2 acre slivers
    ## (This method ensures that slivers adjacent to larger units are preserved)

    ## Split into singlepart polygons
    arcpy.management.MultipartToSinglepart(in_features = outErase, out_feature_class = r'in_memory\Split')

    ## Remove all < 2 acre slivers
    sliverQuery = " POLY_AREA > " + str(sliverSize)
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

    ## Add Acres field
    arcpy.AddGeometryAttributes_management(Input_Features = outIdentity, Geometry_Properties = "AREA", Area_Unit = "ACRES")
    arcpy.management.AlterField(in_table = outIdentity, field = "POLY_AREA", new_field_name = "Acres")

    outUnits_regen = os.path.join(outPath, "PreliminaryRegenUnits")
    arcpy.CopyFeatures_management(outIdentity, outUnits_regen)
    arcpy.AddMessage("Complete")

    # Commercial thin: Merge exclusion layers
    arcpy.AddMessage("Building regeneration harvest units...")
    if arcpy.Exists(outUnits_regen):
        ## Add and populate Exclusion field
        arcpy.management.AddField(in_table = outIdentity, field_name = "Exclusion", field_type = "TEXT", field_length = 30)
        arcpy.management.CalculateField(in_table = outIdentity, field = "Exclusion", expression = "\"Regen harvest unit\"")
        
        ## Use the ListFeatureClasses function to return a list
        env.workspace = outPath
        exclList_ct = arcpy.ListFeatureClasses(wild_card = "excl*")
        if "exclRegenTPA" in exclList_ct:
            exclList_ct.remove("exclRegenTPA")
        if "exclHarvest" in exclList_ct:
            exclList_ct.remove("exclHarvest")
        exclList_ct.append(outIdentity)
        outExclusions = os.path.join(outPath, "PreliminaryCtExclusions")

    arcpy.management.Merge(inputs = exclList_ct, output = outExclusions)
    arcpy.DeleteField_management(outExclusions, ["SETTING_ID", "Acres"])
                                 
    ## Erase exclusions from the project area
    outErase = r'in_memory\Erase'
    arcpy.analysis.Erase(in_features = projectArea, erase_features = outExclusions, out_feature_class = outErase)

    ## Remove all < 2 acre slivers
    ## (This method ensures that slivers adjacent to larger units are preserved)

    ## Split into singlepart polygons
    arcpy.management.MultipartToSinglepart(in_features = outErase, out_feature_class = r'in_memory\Split')

    ## Remove all < 2 acre slivers
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

    outUnits_ct = os.path.join(outPath, "PreliminaryCtUnits")
    arcpy.CopyFeatures_management(outIdentity, outUnits_ct)
    arcpy.AddMessage("Complete")

if __name__ == '__main__':
    # ScriptTool parameters
    parameter0 = projectArea = arcpy.GetParameterAsText(0)
    parameter1 = outPath = arcpy.GetParameterAsText(1)
    parameter2 = clipVegPoly = arcpy.GetParameterAsText(2)
    parameter3 = recruitment = arcpy.GetParameterAsText(3)
    parameter4 = clipRiperian = arcpy.GetParameterAsText(4)
    parameter5 = clipLandtype = arcpy.GetParameterAsText(5)
    parameter6 = clipSpecialUse = arcpy.GetParameterAsText(6)
    parameter7 = clipHarvest = arcpy.GetParameterAsText(7)
    parameter8 = harvestAge = arcpy.GetParameterAsText(8)
    parameter9 = clipMgmtArea = arcpy.GetParameterAsText(9)
    parameter10 = clipLidarSummary = arcpy.GetParameterAsText(10)
    parameter11 = regenTPA = arcpy.GetParameterAsText(11)
    parameter12 = ctTPA = arcpy.GetParameterAsText(12)
    parameter13 = sliverSize = arcpy.GetParameterAsText(13)
    parameter14 = standSplit = arcpy.GetParameterAsText(14)

    ScriptTool(parameter0, parameter1, parameter2, parameter3, parameter4, parameter5, parameter6, parameter7, parameter8, parameter9, parameter10, parameter11, parameter12, parameter13, parameter14)
