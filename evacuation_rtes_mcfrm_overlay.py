# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# overlay_evac_rtes_with_mcfrm.py
#
# Description: Overlay (using the "Identity" tool) the CTPS Evacuation Routes layer with
#              the current and 2050 MC-FRM probability classificaiton polygons.
#              Capture each result in a feature class, and export each output FC to a CSV file.
# ---------------------------------------------------------------------------
#
# Import arcpy module
import arcpy

# CTPS Evacuation Routes
evac_routes = "G:\\Certification_Activities\\Resiliency\\data\\\CTPS_evac_routes\Evacuation_Routes.shp\Evacuation_Routes.shp"

# Road Inventory 2021
road_inv_2021 = r"\\lindalino2\apollo\mpodata\data\roads_gdb\RoadInv2021_and_pavement.gdb\RoadInventory"

# 2050 MC-FRM inundation classification score polygons
probability_score_2050 = "G:\\Certification_Activities\\Resiliency\\data\\mcfrm\\DERIVED_PRODUCTS\\CTPS_classification_mpo_h2o_clip\\CTPS_probability_score_2050_mpo_h2o_clip.shp"
arcpy.AddMessage('2050 classification shapefile: ' + probability_score_2050)
# Current MC-FRM inundation classification score polygons
probability_score_present = "G:\\Certification_Activities\\Resiliency\\data\\mcfrm\\DERIVED_PRODUCTS\\CTPS_classification_mpo_h2o_clip\\CTPS_probability_score_present_mpo_h2o_clip.shp"
arcpy.AddMessage('Current classification shapefile: ' + probability_score_present)

# Read input parameters
# Output Geodatabase
output_gdb = arcpy.GetParameterAsText(0)
# Output directory (i.e., folder) for CSV files
csv_output_dir = arcpy.GetParameterAsText(1)

# Sanity check: Echo input parameters
arcpy.AddMessage('Output GDB: ' + output_gdb)
arcpy.AddMessage('Output folder for CSVs: ' + csv_output_dir)

# Prepatory steps: Flatten Evacuation Routes layer
#
# Prepatory step 1: Perform spatiall join between Road Inventory and Evacuation Routes
#
sj_output_fc = output_gdb + "\\Road_Inv_2021_SJ_Evac_Routes"
arcpy.SpatialJoin_analysis(target_features=road_inv_2021, 
                           join_features=evac_routes, 
						   out_feature_class=sj_output_fc, 
						   join_operation="JOIN_ONE_TO_ONE", 
						   join_type="KEEP_ALL", 
						   field_mapping='Route_ID "Route ID" true true false 16 Text 0 0 ,First,#,RoadInventory,Route_ID,-1,-1;Route_System "Route System" true true false 3 Text 0 0 ,First,#,RoadInventory,Route_System,-1,-1;Route_Number "Route Number" true true false 10 Text 0 0 ,First,#,RoadInventory,Route_Number,-1,-1;Route_Direction "Route Direction" true true false 3 Text 0 0 ,First,#,RoadInventory,Route_Direction,-1,-1;Rd_Seg_ID "Road Segment ID" true true false 4 Long 0 0 ,First,#,RoadInventory,Rd_Seg_ID,-1,-1;F_Class "Functional Class" true true false 2 Short 0 0 ,First,#,RoadInventory,F_Class,-1,-1;F_F_Class "Federal Functional Class" true true false 2 Short 0 0 ,First,#,RoadInventory,F_F_Class,-1,-1;Length "Length" true true false 8 Double 0 0 ,First,#,RoadInventory,Length,-1,-1;Shape_Length "Shape_Length" false true true 8 Double 0 0 ,First,#,RoadInventory,Shape_Length,-1,-1;Shape_Leng "Shape_Leng" true true false 19 Double 0 0 ,First,#,Evacuation_Routes,Shape_Leng,-1,-1;Route_Syst "Route_Syst" true true false 3 Text 0 0 ,First,#,Evacuation_Routes,Route_Syst,-1,-1;Route_Numb "Route_Numb" true true false 10 Text 0 0 ,First,#,Evacuation_Routes,Route_Numb,-1,-1;Route_Dire "Route_Dire" true true false 3 Text 0 0 ,First,#,Evacuation_Routes,Route_Dire,-1,-1;Route_ID_1 "Route_ID_1" true true false 16 Text 0 0 ,First,#,Evacuation_Routes,Route_ID,-1,-1;Evacuation "Evacuation" true true false 5 Long 0 5 ,First,#,Evacuation_Routes,Evacuation,-1,-1', match_option="INTERSECT", search_radius="", distance_field_name="")
#
# Prepatory step 2: Select only those features in (1a) for which (Route_ID = Route_ID_1) AND (Evacuation = 1),
#          i.e., those features in the Spatial Join output that are part of a route designated as
#          possibly being an Evacuation Route (Evacuation = 0 or 1) and that actually are an Evacuation Route (Evacuation = 1).
sj_output_fc_filtered = output_gdb + "\\Road_Inv_2021_Evac_Routes_1"
arcpy.Select_analysis(in_features=sj_output_fc, 
                      out_feature_class=sj_output_fc_filtered,
                      where_clause="( Route_ID  = Route_ID_1 ) AND Evacuation = 1")

# Iterative processing: Perform overlay analysis, once per set of MC-FRM overlay polygons
#
# Overlay FCs
overlay_fcs = [ probability_score_2050, probability_score_present ]
#
# Output FCs and tables
temp = [ "Evac_routes_overlay_2050", "Evac_routes_overlay_present" ]
output_fcs = [ output_gdb + "\\" + fc + "_fc" for fc in temp ]
output_tbls = [ output_gdb + "\\" + fc + "_stats" for fc in temp ]
#
# Output CSV files
# Note because of the way the ESRI table-to-table tool works,
# the output folder and file name are specified _separately_ rater than as a single file path.
output_csv_fns = [ name + '_stats.csv' for name in temp ]

for (overlay_fc, output_fc, output_tbl, output_csv_fn) in zip(overlay_fcs, output_fcs, output_tbls, output_csv_fns):
    s = 'Processing ' + overlay_fc
    arcpy.AddMessage(s)
    # Step 1: Run Identity tool
    arcpy.Identity_analysis(in_features=sj_output_fc_filtered, 
                            identity_features=overlay_fc, 
                            out_feature_class=output_fc, 
                            join_attributes="ALL", cluster_tolerance="", relationship="NO_RELATIONSHIPS")
    # Step 2: Calculate summary statistics table, convert meters to miles, and export to CSV file.
    arcpy.Statistics_analysis(in_table=output_fc,
                              out_table=output_tbl, 
                              statistics_fields="Length SUM", case_field="F_Class;score")
    # Step 3: Add "length_mi" field, and convert meters to miles
    arcpy.AddField_management(in_table=output_tbl, 
                              field_name="length_mi", 
                              field_type="DOUBLE", 
                              field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
    # Step 4: Convert length in meters to miles
    arcpy.CalculateField_management(in_table=output_tbl, 
                                    field="length_mi", 
                                    expression="!SUM_Length! * 0.000621", expression_type="PYTHON_9.3", code_block="")
    # Step 5: Export to CSV file
    arcpy.TableToTable_conversion(in_rows=output_tbl, 
                                  out_path=csv_output_dir, 
                                  out_name=output_csv_fn)
# end_for