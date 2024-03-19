import json
import csv

LINEAR_SCALE_MEASURES = ["perimeter", "width", "height", "longest_path", 
                         "ellipse_major_axis", "ellipse_minor_axis"]
AREA_SCALE_MEASURES = ["area", "convex_hull_area"]

def write_dict_to_csv(input_dict, csv_out_path):

    data_file = open(csv_out_path, "w", newline="")
    csv_writer = csv.writer(data_file)

    count = 0
    header = []
    for obs in input_dict:
        # Write header row
        if (count == 0):
            header = input_dict[obs].keys()
            csv_writer.writerow(header)
            count += 1
        # Make list of obs values to make sure in right order
        working_val_list = []
        for val_name in header:
            working_val_list.append(input_dict[obs][val_name])
        
        csv_writer.writerow(working_val_list)

def is_morpho(obs_name):
    obs_num = obs_name[5:]
    try:
        obs_num_int = int(obs_num)
        if (obs_num_int >= 0):
            return obs_num_int
        else:
            return False
    except ValueError:
        return False
    except Exception as e:
        print(e)
        return False

def load_val(measure_dict):
    """Parse morpho measurements and typecase accordingly."""
    dtype_str = measure_dict["datatype"]
    measure_val = measure_dict["value"]

    if ("'int'" in dtype_str): return int(measure_val)
    elif ("'float'" in dtype_str): return float(measure_val)
    elif ("'bool'" in dtype_str): return bool(dtype_str)
    elif ("'tuple'" in dtype_str): return tuple(dtype_str)  

def scale_linear(val, lin_scale): return val / lin_scale
def scale_area(val, lin_scale): return val / (lin_scale ** 2)

def pcv_convert_morpho(json_in_path, csv_out_path, file_name, 
                       scale_val=None, scale_unit=None, 
                       names_list=None, notes_list=None):

    # Load results file
    with open(json_in_path) as f:
        original_json = json.load(f)
    
    # Put values into dict
    morpho_obs_dict = {}
    for obs_name, obs_dict in original_json["observations"].items():
        obs_number = is_morpho(obs_name)
        if (obs_number):
            morpho_obs_dict[obs_name] = {"observation_name": obs_name}

            # Handle plant names and notes
            if (names_list is not None):
                morpho_obs_dict[obs_name]["sample_name"] = names_list[obs_number]
            
            if (notes_list is not None):
                morpho_obs_dict[obs_name]["sample_note"] = notes_list[obs_number]

            # Load measures
            for measure_name, measure_dict in obs_dict.items():
                morpho_obs_dict[obs_name][measure_name] = load_val(measure_dict)

            # Handle scaling
            if (scale_unit is not None):
                morpho_obs_dict[obs_name][measure_name] = scale_unit

            for measure_name, measure_dict in obs_dict.items():
                
                # Scale linear
                if (measure_name in LINEAR_SCALE_MEASURES):
                    measure_val_unscaled = morpho_obs_dict[obs_name][measure_name]
                    measure_val_scaled = scale_linear(measure_val_unscaled, scale_val)
                    scaled_measure_name = measure_name + "_scaled"
                    morpho_obs_dict[obs_name][scaled_measure_name] = measure_val_scaled

                # Scale area
                elif (measure_name in AREA_SCALE_MEASURES):
                    measure_val_unscaled = morpho_obs_dict[obs_name][measure_name]
                    measure_val_scaled = scale_area(measure_val_unscaled, scale_val)
                    scaled_measure_name = measure_name + "_scaled"
                    morpho_obs_dict[obs_name][scaled_measure_name] = measure_val_scaled

            # Add file name
            morpho_obs_dict[obs_number]["image_name"] = file_name

    write_dict_to_csv(morpho_obs_dict, csv_out_path)