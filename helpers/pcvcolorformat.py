import json
import csv
import numpy as np
import cv2

FREQUENCIES = ['blue_frequencies', 'green_frequencies', 'red_frequencies', 
               'lightness_frequencies', 'green-magenta_frequencies', 'blue-yellow_frequencies', 
               'hue_frequencies', 'saturation_frequencies', 'value_frequencies']

RGB_CHANNELS = ["red", "blue", "green"]

COLOR_ABBREV_REF = {"r":"red", "g":"green", "b":"blue",
                    "l":"lightness","m":"green-magenta","y":"blue-yellow",
                    "h":"hue","s":"saturation","v":"value"}

def merge_dicts(dict1, dict2):
    merge_dict = {}
    for i in dict1.keys():
        merge_dict[i]=dict1[i]
    for i in dict2.keys():
        merge_dict[i]=dict2[i]
    return merge_dict

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

def stdev_color(channel_color_dict: dict, mu: float) -> float:

    val_freq_tups = zip(channel_color_dict["label"], channel_color_dict["value"])
    
    stdev_val = 0.0
    for pixel_value, freq in val_freq_tups:
        percent_float = freq / 100
        dev_val = (pixel_value-mu)**2
        stdev_val += percent_float*dev_val
    
    return stdev_val ** 0.5

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

def calc_channel_references(r_ref, g_ref, b_ref):

    references_dict = {"r": r_ref, "g": g_ref, "b": b_ref}

    rgb_array = np.asarray([[[r_ref, g_ref, b_ref]]], dtype=np.float32)
    
    rgb_arr_scale = rgb_array / 255
    lab_array = cv2.cvtColor(rgb_arr_scale, cv2.COLOR_RGB2LAB)
    l, a, b = lab_array[0,0,:].tolist()
    references_dict["l"] = l
    references_dict["m"] = a
    references_dict["y"] = b

    hsv_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2HSV)
    h, s, v = hsv_array[0,0,:].tolist()
    references_dict["h"] = h
    references_dict["s"] = s
    references_dict["v"] = v

    return references_dict

def calc_channel_correction(vals, refs):
    # inputs as lists in [R,G,B]


    r_val, g_val, b_val = vals
    r_ref, g_ref, b_ref = refs

    return calc_channel_references(r_ref-r_val, g_ref-g_val, b_ref-b_val)

def wb_correction(val, ref):

    return ref - val

def pcv_convert_color(json_in_path, csv_out_path, file_name, color_standard=None, color_refs=None):
    
    # If color standard, should be tuple as (R,G,B)
    # Load in data JSON
    with open(json_in_path) as f:
        original_json = json.load(f)
    
    # calculate color standard values
    if (color_standard is not None):
        color_ref_dict = calc_channel_references(*color_standard)
        color_adj_dict = calc_channel_correction(color_standard, color_refs)

    else:
        color_ref_dict = None
        color_adj_dict = None

    # Calculate color channel means
    color_obs_dict = {}
    for obs_name, obs_dict in original_json["observations"].items():
        if (obs_name.endswith("_color")):
            obs_name_clean = obs_name[:-6]
            color_obs_dict[obs_name_clean] = {"observation_name": obs_name_clean}

            for channel_name, channel_dict in obs_dict.items():
                if ("frequencies" not in channel_name):
                    color_obs_dict[obs_name_clean][channel_name] = channel_dict["value"]
                    continue
                
                # Include file name
                color_obs_dict[obs_name_clean]["image_name"] = file_name

                channel_name_clean = channel_name.split("_")[0]

                channel_arithmetic_mean = mean_color(channel_dict)
                channel_sq_mean = mean_color_sq(channel_dict)

                color_obs_dict[obs_name_clean][channel_name_clean + "_mean"] = channel_arithmetic_mean
                color_obs_dict[obs_name_clean][channel_name_clean + "_sq_mean"] = channel_sq_mean

                channel_amean_stdev = stdev_color(channel_dict, channel_arithmetic_mean)
                channel_sq_stdev = stdev_color(channel_dict, channel_sq_mean)

                color_obs_dict[obs_name_clean][channel_name_clean + "_stdev"] = channel_amean_stdev
                color_obs_dict[obs_name_clean][channel_name_clean + "_sq_stdev"] = channel_sq_stdev

            if (color_standard is not None):
                
                corr_working_dict = {}

                # WB correction on arithmetic mean
                for ref_channel, ref_val in color_adj_dict.items():
                    for channel in color_obs_dict[obs_name_clean].keys():
                        if (channel.startswith(COLOR_ABBREV_REF[ref_channel])) and (channel.endswith("_mean")):
                            corr_working_dict[channel + "_corr_wb"] = color_obs_dict[obs_name_clean][channel] + ref_val

                # WB correction on square mean
                for ref_channel, ref_val in color_adj_dict.items():
                    for channel in color_obs_dict[obs_name_clean].keys():
                        if (channel.startswith(COLOR_ABBREV_REF[ref_channel])) and (channel.endswith("_sq_mean")):
                            corr_working_dict[channel + "_corr_wb"] = color_obs_dict[obs_name_clean][channel] + ref_val

                # Regular correction on arithmetic mean
                for ref_channel, ref_val in color_ref_dict.items():
                    for channel in color_obs_dict[obs_name_clean].keys():
                        if (channel.startswith(COLOR_ABBREV_REF[ref_channel])) and (channel.endswith("_mean")):
                            corr_working_dict[channel + "_corr"] = color_obs_dict[obs_name_clean][channel] - ref_val

                # Regular correction on square mean
                for ref_channel, ref_val in color_ref_dict.items():
                    for channel in color_obs_dict[obs_name_clean].keys():
                        if (channel.startswith(COLOR_ABBREV_REF[ref_channel])) and (channel.endswith("_sq_mean")):
                            corr_working_dict[channel + "_corr"] = color_obs_dict[obs_name_clean][channel] - ref_val

                color_obs_dict[obs_name_clean] = merge_dicts(color_obs_dict[obs_name_clean], corr_working_dict)

    write_dict_to_csv(color_obs_dict, csv_out_path)
