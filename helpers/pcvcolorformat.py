import json
import csv

FREQUENCIES = ['blue_frequencies', 'green_frequencies', 'red_frequencies', 
               'lightness_frequencies', 'green-magenta_frequencies', 'blue-yellow_frequencies', 
               'hue_frequencies', 'saturation_frequencies', 'value_frequencies']

def mean_color(channel_color_dict: dict) -> float:

    val_freq_tups = zip(channel_color_dict["label"], channel_color_dict["value"])

    mean_value = 0
    for pixel_value, freq in val_freq_tups:
        percent_float = freq / 100
        val_abundance = pixel_value * percent_float
        mean_value +=val_abundance

    return mean_value

def mean_color_sq(channel_color_dict: dict) -> float:
    
    val_freq_tups = zip(channel_color_dict["label"], channel_color_dict["value"])

    mean_value = 0
    for pixel_value, freq in val_freq_tups:
        percent_float = freq / 100
        val_abundance = (pixel_value ** 2) * percent_float
        mean_value += val_abundance

    mean_val_unsquared = mean_value ** 0.5

    return mean_val_unsquared

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



def pcv_convert_color(json_in_path, csv_out_path, file_name, color_standard=False):
    
    # If color standard, should be tuple as (R,G,B)
    # Load in data JSON
    with open(json_in_path) as f:
        original_json = json.load(f)

    color_obs_dict = {}

    for obs_name, obs_dict in original_json["observations"].items():
        if (obs_name.endswith("_color")):
            
            obs_name_clean = obs_name[:-6]

            color_obs_dict[obs_name_clean] = {"observation_name": obs_name_clean}

            for channel_name, channel_dict in obs_dict.items():

                if ("frequencies" not in channel_name):
                    color_obs_dict[obs_name_clean][channel_name] = channel_dict["value"]
                    continue


                channel_name_clean = channel_name.split("_")[0]

                channel_arithmetic_mean = mean_color(channel_dict)
                channel_sq_mean = mean_color_sq(channel_dict)

                color_obs_dict[obs_name_clean][channel_name_clean + "_mean"] = channel_arithmetic_mean
                color_obs_dict[obs_name_clean][channel_name_clean + "_sq_mean"] = channel_sq_mean

            color_obs_dict[obs_name_clean]["image_name"] = file_name

    if (color_standard is not False):
        # TODO add the color corrections here

        r_standard, g_standard, b_standard = color_standard

        pass

    write_dict_to_csv(color_obs_dict, csv_out_path)








    