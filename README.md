# evacuation-routes-mc-frm-overlay-analysis

## Overview
This repository contains the tool to perform overlay analysis on CTPS's __Evacuation Routes__ layer and
MC-FRM flood probability overlay polygon layers. The tool currently supports overlay analysis with the 
"current" and 2050 MC-FRM flood probability polygon layers. Extending it to support other flood probability
polygon layers is stragithforward, but was not implemented at this time as it is not currently needed.

## Algorithm
The core of the overlay analysis algorithm is straightforward: it makes use of the ESRI __Identity__ tool.  
The __Evacuation Routes__ layer, however, requires some pre-processing before it can participate in the analysis.
The Evacuation Routes layer is an extract from the Road Inventory's __Routes__ feature class.
This feature supports multiple, concurrent "overlapping" routes: i.e., one stretch of road may carry more
than one set of numbered routes. Unless any overlapping routes are "flattened" into a single route,
overlay analysis risks double- (or, more generically, mulitliple-) counting of route mileage.

The outline of the algorithim therefore is:
1. "Flatten" the Evacuation Routes layer
2. Perform overlay analysis between the restuls of Step \(1\) and the relevant MC-FRM layer using the ESRI __Identity__ tool
3. Calculate total mileage of overlay by functional class and flood probability score 

### Flattening the Evacuation Routes Layer
The method for flattening the Evacuation Routes layer is as follows:
1. Perform a Spatial Join between the Road Inventory and the Evacuation Routes layer
  1. __target\_features__: Road Inventory
  2. __join\_features__: Evacuation Routes
  3. __output\_feature\_class: \(whatever\)
  3. __join\_operation__: JOIN_ONE_TO_ONE
  4. __join\_type__: KEEP_ALL
2. Select all features from the result of Step \(1\) where Route_ID != Route_ID_1, i.e., 
those features for which the Route_ID in the Road Inventory does not match the Route_ID captured by the Spatial Join
3. Delete the selected features.

The Spatial Join operation can - and does - pick up a certain amount of "cruft" from the target\_features.
We use the Route_ID harvested from the Road Inventory on each feature in the output_feature_class to
determine if the feature was or was not in the __join\_features__. If the two Route_IDs of a feature in the
output\_feature\_class are not identical, the feature is discarded.
