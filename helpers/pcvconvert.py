import json
import csv

def format_pcv_json(json_in_path, csv_out_path, scale=-1, names=[], file_name=None, plant_notes=None):
    """
    Formats PlantCV standard JSON output to simple tabular data CSV
    Allows for scaling of area
    Names = List of names to be applied to samples, in order
    """

    # Load in data JSON
    with open(json_in_path) as f:
        original_json = json.load(f)
        
    # Make list of measurements being taken
    # Will become row identifiers in final tabular data
    obs_list = []
    for plant in original_json["observations"]:
        obs_list.append(plant)        
        
    # Make list of measurements being taken
    # Will become column headers in final tabular data
    measurement_list = []
    for measurement in original_json["observations"][obs_list[0]]:
        measurement_list.append(measurement)

    # Construct tabular data in list of lists
    data_list_of_lists = []

    # Add column titles row to data
    column_titles = ["samples"]
    column_titles.extend(measurement_list)

    # Insert in "sample_name" if names provided
    if (names != []):
        column_titles.insert(1, "sample_name")
    
    # Add 'area_scaled' column if scaling coefficient given (scale > 0)
    if (scale > 0):
        column_titles.insert(4, "area_scaled")

    # Add 'image_name' column if one is provided
    if (file_name):
        column_titles.append("image_name")

    # Add 'note' column if one is provided
    if (plant_notes):
        column_titles.append("notes")
        
    # Append column titles to data list   
    data_list_of_lists.append(column_titles)

    # Absolute sample index reference, used for reference to sample name in 'names' list
    true_idx = 0

    # Iterate through samples/observations
    for idx, plant in enumerate(original_json["observations"]):
    
        # Only convert shape analysis images
        if not ((plant.endswith("color")) or (plant.endswith("watershed"))):

            # Create empty list for each sample and append sample name
            plant_val_list = []
            plant_val_list.append(plant)
        
            # Iterate through each measurement of the sample
            for measurement in original_json["observations"][plant]:
            
                # If coordinates in image, break tuple (list) into string
                if (measurement == "center_of_mass") or (measurement == "ellipse_center"):
                    tuple_clean_str = "(" + str(original_json["observations"][plant][measurement]["value"][0]) + "," + str(original_json["observations"][plant][measurement]["value"][1]) + ")"
                    plant_val_list.append(tuple_clean_str)
                
                # Non-coordinates added to data list
                else:
                    plant_val_list.append(original_json["observations"][plant][measurement]["value"])
            
            # Produce column value for 'area_scaled'
            if (scale > 0):
                scaled_value = original_json["observations"][plant]["area"]["value"] / scale
                plant_val_list.insert(3, scaled_value)

            # Insert user-specified name into sample data list
            if (names != []):
                plant_val_list.insert(1, names[true_idx])

            # Add file name column value if sample name is given
            if (file_name):
                plant_val_list.append(file_name)

            # Add provided note to the plant values
            if (plant_notes):
                plant_val_list.append(plant_notes[true_idx])
        
            # Append sample measurements row to tabular list of lists 
            data_list_of_lists.append(plant_val_list)

            # Increment true sample index
            true_idx += 1
    
    # Write tabular data in list of lists to CSV file
    with open(csv_out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(data_list_of_lists)